from unittest.mock import AsyncMock, Mock

import pytest
from telethon.types import Message

from tgtestkit.containers import Keyboard


@pytest.fixture
def inline_keyboard(message_with_inline_keyboard) -> Keyboard:
    return Keyboard(message_with_inline_keyboard)


@pytest.fixture
def reply_keyboard(message_with_reply_keyboard) -> Keyboard:
    return Keyboard(message_with_reply_keyboard)


def test_message_without_buttons():
    mock_msg = Mock(Message)
    mock_msg.buttons = None

    msg = r"The message doesn't have a keyboard."
    with pytest.raises(ValueError, match=msg):
        Keyboard(mock_msg)


def test_keyboard_type_determination(
    message_with_inline_keyboard,
    message_with_reply_keyboard,
):
    reply_keyboard = Keyboard(message_with_reply_keyboard)
    inline_keyboard = Keyboard(message_with_inline_keyboard)

    assert reply_keyboard.is_reply
    assert not reply_keyboard.is_inline

    assert inline_keyboard.is_inline
    assert not inline_keyboard.is_reply


def test_buttons_count(message_with_inline_keyboard):
    ik = Keyboard(message_with_inline_keyboard)

    assert ik.buttons_count == 3


class TestFindButton:
    def test_both_pattern_and_index_passed(self, inline_keyboard):
        msg = r"Exactly one of the `pattern` or `index` arguments must be provided."
        with pytest.raises(ValueError, match=msg):
            inline_keyboard.find_button(pattern="1234", index=33)

    def test_neither_pattern_nor_index_set(self, inline_keyboard):
        msg = r"Exactly one of the `pattern` or `index` arguments must be provided."
        with pytest.raises(ValueError, match=msg):
            inline_keyboard.find_button()

    def test_pattern_exists(self, inline_keyboard):
        button = inline_keyboard.find_button(pattern="with long")

        assert button.text == "Button with long text"

    def test_pattern_doesnt_exist(self, inline_keyboard):
        button = inline_keyboard.find_button(pattern="Button doesn't exist")

        assert button is None

    def test_index_with_zero(self, inline_keyboard):
        button = inline_keyboard.find_button(index=0)
        assert button.text == "Button 1"

    def test_index_negative(self, inline_keyboard):
        button = inline_keyboard.find_button(index=-1)
        assert button.text == "Button 3"

    def test_positive_index(self, inline_keyboard):
        button = inline_keyboard.find_button(index=1)
        assert button.text == "Button with long text"

    def test_index_out_of_range(self, inline_keyboard):
        button = inline_keyboard.find_button(index=4)
        assert button is None


# TODO: add tests for 'click' for different buttons types.
#       (reply, inline, url, etc.)
class TestClick:
    async def test_index_out_of_range(self, inline_keyboard):
        msg = "Button not found. 'pattern=None', 'index=33'"
        with pytest.raises(LookupError, match=msg):
            await inline_keyboard.click(index=33)

    async def test_pattern_doesnt_match(self, inline_keyboard):
        msg = "Button not found. 'pattern=\"Doesn't exist\"', 'index=None'"
        with pytest.raises(LookupError, match=msg):
            await inline_keyboard.click(pattern="Doesn't exist")

    async def test_success_call(self, inline_keyboard):
        button = inline_keyboard.find_button(index=1)
        button.click = AsyncMock()

        await inline_keyboard.click(index=1)

        button.click.assert_awaited_once()
