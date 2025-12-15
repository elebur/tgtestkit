from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from telethon import TelegramClient
from telethon.events.common import EventBuilder


@asynccontextmanager
async def add_handlers_transient(
    client: TelegramClient,
    handlers: list[
        tuple[
            Callable[[EventBuilder], Awaitable[Any]],
            EventBuilder,
        ]
    ],
) -> AsyncGenerator:
    """
    Register a one-time/ad-hoc telethon's event handlers.

    These handlers are only valid during the context manager body.

    Args:
        client (telethon.TelegramClient): configured telethon TelegramClient.
        handlers (list[tuple[]]): list of tuples each contains three items.
            handler (Callable[[EventBuilder], Awaitable[Any]]): The callable to invoke
                when  an event occurs. This is often just a function object.
            event (EventBuilder): The event type to bind to the handler. When Telegram
                sends an update corresponding to this type, handler is called with
                an instance of this event type as the only argument.
    """
    for handler, event in handlers:
        client.add_event_handler(handler, event)

    yield

    for handler, event in handlers:
        client.remove_event_handler(handler, event)
