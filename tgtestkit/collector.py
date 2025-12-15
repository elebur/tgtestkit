# ruff: noqa: DTZ003
"""Standalone `collector` utilities."""
import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from telethon.errors import RPCError
from telethon.events import Raw
from telethon.events.common import EventCommon

from tgtestkit.exceptions import ExpectationError
from tgtestkit.expectation import Expectation
from tgtestkit.handler_utils import add_handlers_transient
from tgtestkit.timeout_settings import TimeoutSettings

if TYPE_CHECKING:
    from tgtestkit.botcontroller import BotController

from tgtestkit.containers.responses import Response
from tgtestkit.update_recorder import UpdateRecorder

logger = logging.getLogger(__name__)


# TODO: rewrite as a class?
@asynccontextmanager
async def collect(
    controller: "BotController",
    handlers: list[EventCommon],
    *,
    unhandled_updates: bool,
    expectation: Expectation | None = None,
    timeouts: TimeoutSettings | None = None,
) -> AsyncGenerator[Response]:
    """
    Gather updates based on the `handlers` and wait with respect to `expectation`.

    This is a context manager.

    Args:
        controller (BotController): an instance of BotController.
        handlers (list[EventCommon]): a list of events to record updates for.
        unhandled_updates (bool): whether to save updates that were not caught by
            `handlers`.
        expectation (optional): configured `Expectation` instance. Defaults to None.
        timeouts (optional): configured `TimeoutSettings` instance. Defaults to None.

    Raises:
        InvalidResponseError: raised if no updates were received within
            the given timeout and `TimeoutSettings.raise_on_timeout` is set to `True`

    Yields:
        AsyncGenerator[Response]: _description_
    """
    expectation = expectation or Expectation()
    timeouts = timeouts or TimeoutSettings()

    recorder = UpdateRecorder()

    temp_handlers = [(recorder.record_update, h) for h in handlers]

    # This handler will save all other events that were not caught.
    if unhandled_updates:
        temp_handlers.append(
            (recorder.record_unhandled_updates, Raw),
        )

    await controller.start()

    async with add_handlers_transient(controller.client, temp_handlers):
        response = Response(controller, recorder)

        logger.debug("Collector set up. Executing user-defined interaction...")
        yield response  # Start user-defined interaction
        logger.debug("interaction complete.")

        num_received = 0
        timeout_end = datetime.utcnow() + timedelta(seconds=timeouts.max_wait)

        try:
            seconds_remaining = (timeout_end - datetime.utcnow()).total_seconds()

            while True:
                if seconds_remaining > 0:
                    # Wait until we receive any message or time out
                    logger.debug(f"Waiting for message #{num_received + 1}")
                    await asyncio.wait_for(
                        recorder.wait_until(
                            lambda updates: expectation.is_sufficient(updates)
                            or len(updates) > num_received
                        ),
                        timeout=seconds_remaining,
                    )

                num_received = len(recorder.updates)

                if timeouts.wait_consecutive:
                    # Always wait for at least `wait_consecutive`
                    # seconds for another message.
                    try:
                        logger.debug(
                            f"Checking for consecutive message to #{num_received}...",
                        )
                        await asyncio.wait_for(
                            recorder.wait_until(
                                lambda updates: len(updates) > num_received),
                                # The consecutive end may go over the max wait timeout,
                                # which is a design decision.
                                timeout=timeouts.wait_consecutive,
                        )
                        logger.debug("received 1.")
                    except TimeoutError:
                        logger.debug("none received.")

                num_received = len(recorder.updates)

                if expectation.is_sufficient(recorder.updates):
                    expectation.verify(recorder.updates, timeouts)
                    return

                seconds_remaining = (timeout_end - datetime.utcnow()).total_seconds()

                assert seconds_remaining is not None

                if seconds_remaining <= 0:
                    expectation.verify(recorder.updates, timeouts)
                    return

        except RPCError as ex:
            # Internal Telegram error
            # https://core.telegram.org/api/errors#500-internal
            if 500 <= ex.code < 600:  # noqa: PLR2004
                logger.warning(ex)
                # TODO: code can get into the infinity loop here.
                await asyncio.sleep(60)
            else:
                raise
        except asyncio.exceptions.TimeoutError as te:
            if timeouts.raise_on_timeout:
                raise ExpectationError from te
            else:
                # TODO: better warning message
                logger.warning("Peer did not reply.")
        finally:
            recorder.stop()
            await controller.stop()
