import time
from unittest.mock import patch as mock_patch

from freezegun import freeze_time


async def test_without_last_response_ts(mock_controller):
    # By default the controller's '_last_response_ts' is None.
    with mock_patch("asyncio.sleep", autospec=True) as mock_asleep:
        await mock_controller._wait_if_necessary()

    mock_asleep.assert_not_awaited()


async def test_without_global_action_delay(mock_controller):
    mock_controller.global_action_delay = None
    mock_controller._last_response_ts = time.time() + 1

    with mock_patch("asyncio.sleep", autospec=True) as mock_asleep:
        await mock_controller._wait_if_necessary()

    mock_asleep.assert_not_awaited()


@freeze_time("2025-11-30")
async def test_with_delay(mock_controller):
    mock_controller._last_response_ts = time.time() + 1
    with mock_patch("asyncio.sleep", autospec=True) as mock_asleep:
        await mock_controller._wait_if_necessary()

    mock_asleep.assert_awaited_once()
    # Because of the Floating-Point precision issues the actual
    # value of the args won't be 1.8 but something like 1.79999995231628
    # https://docs.python.org/3.14/tutorial/floatingpoint.html
    #
    # The 'await' args is a sequence of tuples.
    assert 1.79 < mock_asleep.await_args[0][0] <= 1.8
