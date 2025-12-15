import pytest
from telethon import TelegramClient

from tgtestkit import BotController


@pytest.mark.network
async def test_ensure_preconditions_for_all_peers_with_bot_peer(
    client: TelegramClient, test_bot_username,
):
    assert not client.is_connected()

    controller = BotController(client, test_bot_username)
    async def outer_caller():
        await controller._ensure_preconditions()

    await outer_caller()
    assert controller.client.is_connected()


@pytest.mark.network
async def test_ensure_preconditions_for_all_peers_with_user_peer(
    client: TelegramClient, test_user_username,
):
    assert not client.is_connected()

    controller = BotController(client, test_user_username)
    async def outer_caller():
        await controller._ensure_preconditions()

    await outer_caller()
    assert controller.client.is_connected()


@pytest.mark.network
async def test_ensure_preconditions_for_bots_with_user_peer(
    client: TelegramClient, test_user_username,
):
    assert not client.is_connected()

    controller = BotController(client, test_user_username)
    async def outer_caller() -> None:
        await controller._ensure_preconditions(bots_only=True)

    msg = (
        f"The 'outer_caller' expects the peer to be a bot, "
        f"but '{test_user_username}' is not a bot."
    )
    with pytest.raises(ValueError, match=msg):
        await outer_caller()

    assert controller.client.is_connected()


@pytest.mark.network
async def test_ensure_preconditions_for_bots_with_bot_peer(
    client: TelegramClient, test_bot_username,
):
    assert not client.is_connected()

    controller = BotController(client, test_bot_username)
    async def outer_caller() -> None:
        await controller._ensure_preconditions(bots_only=True)

    await outer_caller()
    assert controller.client.is_connected()


@pytest.mark.network
async def test_custom_peer_with_wrong_type(client, test_bot_username, test_user_username):

    await client.connect()

    controller = BotController(client, test_bot_username)
    async def outer_caller() -> None:
        await controller._ensure_preconditions(bots_only=True, peer="durov")

    msg = ("'peer' must an instance of `telethon.tl.types.User`. "
            "Got <class 'telethon.tl.types.Channel'> instead.")

    with pytest.raises(TypeError, match=msg):
        await outer_caller()


@pytest.mark.network
async def test_custom_peer_bots_only_user_peer(client, test_bot_username, test_user_username):

    await client.connect()

    controller = BotController(client, test_bot_username)
    async def outer_caller() -> None:
        await controller._ensure_preconditions(
            bots_only=True,
            peer=test_user_username,
        )

    msg = (
        f"The 'outer_caller' expects the peer to be a bot, "
        f"but '{test_user_username}' is not a bot."
    )

    with pytest.raises(ValueError, match=msg):
        await outer_caller()


@pytest.mark.network
async def test_custom_peer_bots_only_bot_peer(
    client,
    test_bot_username,
):

    await client.connect()

    controller = BotController(client, test_bot_username)
    async def outer_caller() -> None:
        await controller._ensure_preconditions(
            bots_only=True,
            peer="gif",
        )

    await outer_caller()
    assert controller.client.is_connected()
