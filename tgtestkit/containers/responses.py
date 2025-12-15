from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType as frozendict  # noqa: N813
from typing import TYPE_CHECKING

from telethon.types import Message

from tgtestkit.containers import Keyboard
from tgtestkit.update_recorder import UpdateRecorder

if TYPE_CHECKING:
    from tgtestkit.botcontroller import BotController


def _build_message_id(message: Message) -> int:
    """
    Build a unique identifier for the 'message`.

    This identifier will be used as a key in the keyboards dict in `Response`.
    """
    return int(f"{message.peer_id.user_id}{message.id}")


class Response:
    def __init__(self, controller: "BotController", recorder: UpdateRecorder) -> None:
        self._controller = controller
        self._recorder = recorder

        # cached properties
        self.__keyboards: Mapping[int, Keyboard] = {}
        self.__messages: list[Message] = []

    def __str__(self) -> str:  # noqa: D105
        if not self.has_messages:
            return "Empty response"

        divider_top = "  Message #{}  ".center(81, "=") + "\n"
        divider_bottom = "".center(80, "=") + "\n\n\n"
        final_string = ""
        for i, msg in enumerate(self.messages):
            final_string += divider_top.format(i+1)
            final_string += msg.message + "\n"
            final_string += divider_bottom

        return final_string

    @property
    def messages(self) -> list[Message]:
        """
        Return only messages from the updates.

        The list of messages is cached on the first call.
        """
        if not self.__messages:
            for update in self._recorder.updates:
                if (message := getattr(update, "message", None)):  # noqa: SIM102
                    # In some updates 'message' attribute may refer
                    # to a `str` instance.
                    if isinstance(message, Message):
                        self.__messages.append(message)

        return self.__messages

    @property
    def has_messages(self) -> bool:
        """Return `True` if the response has at least one message."""
        return bool(self.messages)

    @property
    def _keyboards(self) -> Mapping[int, Keyboard]:
        """
        Get a mapping to all available keyboards.

        The key is `telethon.types.Message` and the value is an associated keyboards
        or an empty mapping if there is no keyboard in the message.

        Returns:
            Mapping[Message, InlineKeyboard | ReplyKeyboard]: _description_
        """
        if self.__keyboards:
            return frozendict(self.__keyboards)
        if not self.has_messages:
            return frozendict({})

        result_dict = {}
        for msg in self.messages:
            msg_key = _build_message_id(msg)
            if msg.buttons:
                result_dict[msg_key] = Keyboard(msg)
            else:
                result_dict[msg_key] = frozendict({})

        self.__keyboards = result_dict
        return frozendict(result_dict)

    def get_keyboard(self, message: Message) -> Keyboard | None:
        """Return a keyboard for the given 'message' or `None`."""
        return self._keyboards.get(_build_message_id(message), None)

    @property
    def reply_keyboard(self) -> Keyboard | None:
        """
        Return the most recent ReplyKeyboard.

        If Telegram sends multiple messages with reply keyboards, only the last
        keyboard will be shown in the Telegram UI.

        All other keyboards can be accessed through the `Response.keyboards` property.

        Returns:
            ReplyKeyboard | None: `None` if there is no ReplyKeyboards in messages.
        """
        for message, keyboard in reversed(self._keyboards.items()):
            if keyboard and keyboard.is_reply:
                return keyboard

        return None

    @property
    def last_message(self) -> Message | None:
        """Return the most recent message."""
        if not self.has_messages:
            return None

        return self.messages[-1]

    @property
    def last_message_datetime(self) -> datetime | None:
        """Return time of the last message as `datetime` object."""
        return None if not self.has_messages else self.last_message.date

    @property
    def last_message_timestamp(self) -> float | None:
        """Return time of the last message as a timestamp."""
        if self.last_message_datetime:
            return self.last_message_datetime.timestamp()

        return None

    def get_reply_keyboards(self) -> list[Keyboard]:
        """Return all Reply `Keyboard`s that were collected for the response."""
        return [kb for kb in self._keyboards.values() if kb and kb.is_reply]

    def get_inline_keyboards(self) -> list[Keyboard]:
        """Return all Inline `Keyboard`s that were collected for the response."""
        return [kb for kb in self._keyboards.values() if kb and kb.is_inline]
