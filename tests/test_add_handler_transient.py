from telethon.events import MessageEdited, NewMessage

from tgtestkit.handler_utils import add_handlers_transient


async def _handler_placeholder(event):
    pass


async def test_without_filters(client):
    assert len(client.list_event_handlers()) == 0

    async with add_handlers_transient(client,
        [(_handler_placeholder, NewMessage())],
    ):
        assert len(client.list_event_handlers()) == 1

    assert len(client.list_event_handlers()) == 0


async def test_with_existing_handlers(client):
    async def cb(e):
        pass

    client.add_event_handler(cb, MessageEdited)

    assert len(client.list_event_handlers()) == 1

    async with add_handlers_transient(client, [(
        _handler_placeholder, NewMessage,
    )]):
        assert len(client.list_event_handlers()) == 2

    assert len(client.list_event_handlers()) == 1
