from unittest.mock import patch as mock_patch

import pytest
from telethon import TelegramClient

from tgtestkit import BotController


@pytest.mark.network
async def test_initialize(client: TelegramClient, test_bot_username):
    controller = BotController(client, test_bot_username)

    await controller.start()

    assert controller.client.is_connected()
    assert controller._target_peer.username == "BotFather"
    assert controller._dispatcher_task


async def test_disconnected_client(mock_controller):
    mock_controller.client.is_connected.return_value = False

    await mock_controller.start()

    mock_controller.client.connect.assert_awaited_once()


async def test_starting_dispatcher_task(mock_controller):
    mock_controller._dispatcher_task = None
    mock_controller.client.is_connected.return_value = True

    with mock_patch("asyncio.create_task") as mock_aiotask:
        await mock_controller.start()

    mock_aiotask.assert_called_once()


async def test_reconnect_client(mock_controller):
    mock_controller.client.is_connected.return_value = False

    await mock_controller.start()

    mock_controller.client.get_me.assert_awaited_once()
