import time
from unittest.mock import AsyncMock
from unittest.mock import patch as monkey_patch

import pytest

from tgtestkit import BotController
from tgtestkit.exceptions import ExpectationError


@pytest.mark.network
async def test_collect_with_default_args(controller: BotController):
    async with controller.collect_messages() as response:
        await controller.send_command("/cancel")

    assert len(response.messages) == 1


async def test_malformed_handlers(controller: BotController):
    with pytest.raises(ValueError, match=r"One of \(or all\) of.*"):
        async with controller.collect_messages(
            new_messages=False, edited_messages=False, unhandled_updates=False,
        ):
            pass


@pytest.mark.network
async def test_additional_peers(controller: BotController):
    async with controller.collect_messages(2, additional_peers=("gif", )) as response:
        await controller.send_command("/cancel")
        await controller.client.send_message("gif", "hello")

    assert len(response.messages) == 2

    async with controller.client:
        for msg in response.messages:
            await msg.get_sender()

    usernames = set()
    usernames.add(response.messages[0].sender.username)
    usernames.add(response.messages[1].sender.username)

    assert usernames == {"gif", "BotFather"}


@pytest.mark.network
async def test_max_wait(controller):
    start_time = time.time()
    with pytest.raises(ExpectationError):
        async with controller.collect_messages(
            max_wait=1,
        ) as response:
            await controller.client.send_message("gif", "cancel")

    diff_time = time.time() - start_time

    # It takes a little more than one second.
    assert 1 < diff_time < 2


@pytest.mark.network
async def test_no_raise(controller):
    async with controller.collect_messages(
        max_wait=1,
        raise_=False,
    ) as response:
            await controller.client.send_message("gif", "cancel")

    assert not response.has_messages


async def test_context_manager(mock_controller):
    with (
        monkey_patch("tgtestkit.collector.UpdateRecorder") as mock_recorder,
        monkey_patch("asyncio.wait_for") as mock_wait_for,
    ):
        mock_controller.start = AsyncMock()
        mock_controller._dispatcher_task = AsyncMock()
        mock_controller.stop = AsyncMock()
        async with mock_controller.collect_messages(max_wait=0.01, raise_=False) as response:
            mock_recorder.assert_called_once()
            mock_controller.start.assert_awaited_once()

        # mock.patch returns a mock callable and its 'return_value' is
        # an actual instance.
        mock_recorder.return_value.stop.assert_called_once()
        mock_controller.stop.assert_awaited_once()
