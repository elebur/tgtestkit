import logging
from dataclasses import dataclass

from telethon.events.common import EventCommon

from tgtestkit.exceptions import ExpectationError
from tgtestkit.timeout_settings import TimeoutSettings
from tgtestkit.utils.sentinel import NotSet

logger = logging.getLogger(__name__)


@dataclass
class Expectation:
    """
    Defines the expected reaction of a peer.

    Attributes:
        min_updates (int): Minimum number of expected messages.
        max_updates (int): Maximum number of expected messages.
    """

    # TODO: get rid of NotSet.
    min_updates: int | type[NotSet] = NotSet
    max_updates: int | type[NotSet] = NotSet

    def is_sufficient(self, updates: list[EventCommon]) -> bool:
        """Check if there is at least 'min_updates' updates."""
        n = len(updates)
        if self.min_updates is NotSet:
            return n >= 1
        return n >= self.min_updates

    def _is_match(self, updates: list[EventCommon]) -> bool:
        """Check whether there is more than min updates and less than max."""
        n = len(updates)
        return (self.min_updates is NotSet or n >= self.min_updates) and (
            self.max_updates is NotSet or n <= self.max_updates
        )

    def verify(self, updates: list[EventCommon], timeouts: TimeoutSettings) -> None:
        """
        Check that the number of updates is as expected.

        Args:
            updates (list[EventCommon]):
            timeouts (TimeoutSettings):
        """
        if self._is_match(updates):
            return

        n = len(updates)

        if n < self.min_updates:
            _raise_or_log(
                timeouts,
                "Expected {} updates but only received {} after waiting {} seconds.",
                self.min_updates,
                n,
                timeouts.max_wait,
            )
            return

        if n > self.max_updates:
            _raise_or_log(
                timeouts,
                "Expected only {} updates but received {}.",
                self.max_updates,
                n,
            )
            return


def _raise_or_log(timeouts: TimeoutSettings, msg: str, *fmt) -> None:
    if timeouts.raise_on_timeout:
        if fmt:
            raise ExpectationError(msg.format(*fmt))
        else:
            raise ExpectationError(msg)
    logger.debug(msg.format(*fmt))
