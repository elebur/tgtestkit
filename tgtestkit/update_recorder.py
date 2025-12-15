import asyncio
import logging
from collections.abc import Callable

from telethon.events.common import EventCommon

logger = logging.getLogger(__name__)

Predicate = Callable[[list[EventCommon]], bool]


class UpdateRecorder:
    """
    Save all incoming updates (that have passed user's filters).

    Allow waiting while updates will met certain conditions.
    """

    def __init__(self) -> None:
        logger.debug("Creating new UpdateRecorder")
        self.updates: list[EventCommon] = []
        self._lock = asyncio.Lock()

        self._any_received = asyncio.Event()
        # The list of predicates and associated asyncio events.
        self._event_conditions: list[
            tuple[Predicate, asyncio.Event]
        # This initial predicate will fire when the first update will arrive.
        # This is how the predicate is look like `bool(save.updates)`
        ] = [(bool, self._any_received)]

        self.unhandled_updates: list[EventCommon] = []
        self._is_completed = False

    def __len__(self) -> int:
        """Return the count of the recorded updates."""
        return len(self.updates)

    def stop(self) -> None:
        """After this method is called all incoming updates will be ignored."""
        self._is_completed = True

    async def record_update(self, update: EventCommon) -> None:
        """
        Save incoming update and check all stored updates against registered predicates.

        Predicates are registered by the 'wait_until' method. An example of a predicate:
        `lambda updates: len(updates) > 3`

        Args:
            update (EventCommon): incoming update.
        """
        if self._is_completed:
            logger.debug(f"UpdateRecorder is completed. Ignoring the update {update}")
            return

        logger.debug(f"Saving the update '{update}'")
        async with self._lock:
            self.updates.append(update)
            for (predicate, aio_event) in self._event_conditions:
                if predicate(self.updates):
                    aio_event.set()

    async def wait_at_least_one(self) -> None:
        """`asyncio.Event` that waits when at least one update will be recorded."""
        await self._any_received.wait()

    async def wait_until(self, predicate: Predicate) -> None:
        """
        Wait until the predicate returns True.

        Predicates are run against the inner list of all registered updates.
        Args:
            predicate (Predicate): a function that accepts one argument which is
                a list of updates and returns `bool`.

        Examples:
            ``` python
            recorder = Recorder()
            ...
            # Wait until recorder receives three updates.
            await recorder.wait_until(lambda updates: len(updates) > 3)
            ```
        """
        async with self._lock:
            if predicate(self.updates):
                return

            ev = asyncio.Event()
            self._event_conditions.append((predicate, ev))

        await ev.wait()

    async def record_unhandled_updates(self, update: EventCommon) -> None:
        """Save all updates that were not caught by user defined handlers."""
        logger.debug(f"Saving unhandled update '{update}'")
        self.unhandled_updates.append(update)
