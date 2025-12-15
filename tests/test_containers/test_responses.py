import datetime
import random
from dataclasses import dataclass
from unittest.mock import Mock, PropertyMock

import pytest
from telethon.events import CallbackQuery, InlineQuery
from telethon.types import Message

from tgtestkit import BotController
from tgtestkit.containers.responses import Response
from tgtestkit.update_recorder import UpdateRecorder

MockMessage = Mock(Message)


@dataclass
class Event:
    """Placeholder for the Telethon's EventCommon."""

    message: Message | str | None = None


@pytest.fixture
def fake_controller() -> BotController:
    return Mock(spec=BotController)


@pytest.fixture
def recorder() -> UpdateRecorder:
    return UpdateRecorder()


class TestMessagesProperty:
    def test_dunder_str(self, fake_controller, recorder):
        messages_count = 3
        type(MockMessage).message = PropertyMock(
            side_effect=["text1", "text2", "text3"],
        )

        response = Response(fake_controller, recorder)
        response._Response__messages.extend([MockMessage] * messages_count)

        expected_output = (
            "=================================  Message #1  =================================\n"
            "text1\n"
            "================================================================================\n"
            "\n\n"
            "=================================  Message #2  =================================\n"
            "text2\n"
            "================================================================================\n"
            "\n\n"
            "=================================  Message #3  =================================\n"
            "text3\n"
            "================================================================================\n"
            "\n\n"
        )
        assert str(response) == expected_output

    def test_without_messages(self, fake_controller, recorder):
        response = Response(fake_controller, recorder)

        assert not response.messages

    def test_with_messages(self, fake_controller, recorder):
        messages_count = 3
        response = Response(fake_controller, recorder)
        recorder.updates.extend([Event(message=MockMessage)] * messages_count)

        assert response.messages
        assert len(response.messages) == messages_count

    def test_with_messages_and_other_type_of_updates(self, fake_controller, recorder):
        response = Response(fake_controller, recorder)

        updates = []
        # Updates with valid messages.
        updates.extend([
            Event(message=MockMessage),
            Event(message=MockMessage),
            Event(message=MockMessage),
            Event(message=MockMessage),
        ])

        # Populating updates with non-message updates.
        updates.extend([
            Event(message="1"),
            Event(message="1"),
            Event(message="2"),
            Event(message="3"),
            Event(message=Mock(CallbackQuery)),
            Event(message=Mock(CallbackQuery)),
            Event(message=Mock(InlineQuery)),
            Event(message=Mock(InlineQuery)),
        ])

        random.shuffle(updates)

        recorder.updates.extend(updates)
        assert response.messages
        assert len(response.messages) == 4


class TestHasMessages:
    def test_with_no_messages(self, fake_controller, recorder):
        response = Response(fake_controller, recorder)

        assert not response.has_messages

    def test_when_messages_exist(self, fake_controller, recorder):
        messages_count = 3
        response = Response(fake_controller, recorder)
        recorder.updates.extend([Event(message=MockMessage)] * messages_count)

        assert response.has_messages

class TestLastMessageDateTimeAndLastMessageTimestamp:
    def test_without_messages(self, fake_controller, recorder):
        response = Response(fake_controller, recorder)

        assert response.last_message_datetime is None
        assert response.last_message_timestamp is None

    def test_with_messages(self, fake_controller, recorder):
        response = Response(fake_controller, recorder)
        m1 = Mock(Message)
        m2 = Mock(Message)
        m3 = Mock(Message)

        m1.date = datetime.datetime(2023, 1, 2, 9, 10, 55)
        m2.date = datetime.datetime(2024, 11, 22, 7, 1, 5)
        m3.date = datetime.datetime(2025, 12, 25, 17, 22, 33)

        recorder.updates.extend([
            Event(message=m1),
            Event(message=m2),
            Event(message=m3),
        ])

        assert response.last_message_datetime == datetime.datetime(
            2025, 12, 25, 17, 22, 33
        )
        assert response.last_message_timestamp == 1766676153.0
