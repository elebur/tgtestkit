import itertools
import logging
import pprint
import re
from re import Pattern

from telethon.tl.custom.messagebutton import MessageButton
from telethon.tl.types.messages import BotCallbackAnswer
from telethon.types import Message

logger = logging.getLogger(__name__)

URL = str


class Keyboard:
    """
    Represents a keyboard.

    It might be either an Inline or a Reply keyboard.
    """

    def __init__(self, message: Message) -> None:
        if not message.buttons:
            msg = "The message doesn't have a keyboard."
            raise ValueError(msg)

        self._keyboard: list[list[MessageButton]] = message.buttons
        self._message = message

    def __str__(self):
        """Return a textual representation of the keyboard."""
        keyboard = []
        for row in self._keyboard:
            keyboard.append(  # noqa: PERF401
                [button.text for button in row],
            )

        return pprint.pformat(keyboard, indent=2)

    @property
    def buttons_count(self) -> int:
        """Return the number of buttons."""
        return self._message.button_count

    @property
    def is_inline(self) -> bool:
        """`True` if this is an inline keyboard."""
        b = self._keyboard[0][0]
        # A Reply keyboard has only the 'text' attribute, while
        # an Inline keyboard might have one of these.
        return bool(b.data or b.url or b.inline_query)

    @property
    def is_reply(self) -> bool:
        """`True` if this is a Reply keyboard."""
        # A keyboard could be either a Reply or Inline one.
        # If this not an Inline keyboard, then it is a Reply one.
        return not self.is_inline

    def find_button(
        self,
        pattern: Pattern | str | None = None,
        index: int | None = None,
    ) -> MessageButton | None:
        """
        Attempt to find a `MessageButton` by its text in the keyboard.

        Search anywhere in the underlying 'keyboard', by matching the button
        captions with the given `pattern` or its global `index`.
        If no button could be found, `None` will be returned.

        The `pattern` and `index` arguments are mutually exclusive.

        Args:
            pattern: The button caption to look for (by `re.search`).
            index: The index of the button, counting from
                top left to bottom right and starting at 0.

        Returns:
            `telethon.types.buttons.Callback` or `telethon.types.buttons.Callback`
                if found, else `None`.
        """
        index_set = isinstance(index, int)
        if not any((pattern, index_set)) or all((pattern, index_set)):
            msg = "Exactly one of the `pattern` or `index` arguments must be provided."
            raise ValueError(msg)

        if pattern:
            compiled = re.compile(pattern)
            for row in self._keyboard:
                for button in row:
                    if compiled.search(button.text):
                        return button
            return None
        elif index_set:
            buttons_flattened = list(
                itertools.chain.from_iterable(self._keyboard),
            )
            try:
                return buttons_flattened[index]
            # Raised when the 'index' is out of range.
            except IndexError:
                return None

        return None

    async def click(
        self,
        pattern: Pattern | str | None = None,
        index: int | None = None,
        **kwargs,
    ) -> Message | BotCallbackAnswer | URL:
        """
        Click a button.

        Uses `find_button` with the given `pattern` or `index`,
        clicks the button if found, and waits for the bot to react in the same chat.

        If not button could be found, `LookupError` will be raised.

        Args:
            pattern (Pattern | str | None, optional): The button caption to look
                for (by `re.search`). Defaults to None.
            index (int | None, optional): The index of the button, counting
                from top left to bottom right and starting at 0.
                [
                    [0, 1, 2],
                    [   3   ],
                    [4,    5]
                ]
                Defaults to None.
            **kwargs: will be sent to the Telethon's `MessageButton.click()` method.
                Possible values can be found here:
                https://docs.telethon.dev/en/stable/modules/custom.html#telethon.tl.custom.messagebutton.MessageButton.click

        Raises:
            LookupError: if the button couldn't be found.
        """
        button: MessageButton = self.find_button(pattern, index)
        if not button:
            msg = f"Button not found. '{pattern=}', '{index=}'"
            raise LookupError(msg)

        return await button.click(**kwargs)
