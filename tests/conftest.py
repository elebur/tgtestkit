import datetime
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from dotenv import dotenv_values
from telethon import TelegramClient
from telethon.tl.custom.messagebutton import MessageButton
from telethon.tl.types import (
    KeyboardButton,
    KeyboardButtonCallback,
    KeyboardButtonRow,
    PeerUser,
    ReplyInlineMarkup,
    ReplyKeyboardMarkup,
    User,
    UserProfilePhoto,
    UserStatusOffline,
)
from telethon.types import Message

from tgtestkit.botcontroller import BotController

TEST_ENV_VARS = dotenv_values(".env.tests")


@pytest.fixture
def client() -> Generator[TelegramClient, None, None]:
    session_file = Path(TEST_ENV_VARS["SESSION_FILE_PATH"])
    if not session_file.exists():
        msg = f"The session file couldn't be found '{session_file.absolute()}'"
        raise FileNotFoundError(msg)

    client = TelegramClient(
        session_file,
        api_id=int(TEST_ENV_VARS["TELEGRAM_API_ID"]),
        api_hash=TEST_ENV_VARS["TELEGRAM_API_HASH"],
    )

    yield client

    client.disconnect()


@pytest.fixture
def mock_client() -> TelegramClient:
    mock_client = AsyncMock(spec=TelegramClient)
    mock_client.connected = True

    return mock_client


@pytest.fixture
def test_user_username():
    return "kimdotcom"


@pytest.fixture
def test_bot_username():
    return "BotFather"


@pytest.fixture
def fake_botfather_user() -> User:
    return User(
        id=93372553,
        is_self=False,
        contact=False,
        mutual_contact=False,
        deleted=False,
        bot=True,
        bot_chat_history=False,
        bot_nochats=True,
        verified=True,
        restricted=False,
        min=False,
        bot_inline_geo=False,
        support=False,
        scam=False,
        apply_min_photo=True,
        fake=False,
        bot_attach_menu=False,
        premium=False,
        attach_menu_enabled=False,
        bot_can_edit=False,
        close_friend=False,
        stories_hidden=False,
        stories_unavailable=True,
        contact_require_premium=False,
        bot_business=False,
        bot_has_main_app=True,
        bot_forum_view=False,
        access_hash=12345678910111213,
        first_name='BotFather',
        last_name=None,
        username='BotFather',
        phone=None,
        photo=UserProfilePhoto(
            photo_id=401032061935265706,
            dc_id=1,
            has_video=False,
            personal=False,
            stripped_thumb=b'\x01\x08\x08\x9f\xcf\x7f\xb4\x17\xecd\xd9E\x14P\x16?'
        ),
        status=None,
        bot_info_version=27,
        restriction_reason=[
        ],
        bot_inline_placeholder=None,
        lang_code=None,
        emoji_status=None,
        usernames=[
        ],
        stories_max_id=None,
        color=None,
        profile_color=None,
        bot_active_users=3518777,
        bot_verification_icon=None,
        send_paid_messages_stars=None,
    )


@pytest.fixture
def fake_user() -> User:
    return User(
        id=1234567890,
        is_self=False,
        contact=False,
        mutual_contact=False,
        deleted=False,
        bot=False,
        bot_chat_history=False,
        bot_nochats=False,
        verified=False,
        restricted=False,
        min=False,
        bot_inline_geo=False,
        support=False,
        scam=False,
        apply_min_photo=True,
        fake=False,
        bot_attach_menu=False,
        premium=False,
        attach_menu_enabled=False,
        bot_can_edit=False,
        close_friend=False,
        stories_hidden=False,
        stories_unavailable=True,
        contact_require_premium=False,
        bot_business=False,
        bot_has_main_app=False,
        bot_forum_view=False,
        access_hash=109876543210123456,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        phone=None,
        photo=None,
        status=UserStatusOffline(
            was_online=datetime.datetime(
                2025, 1, 2, 3, 4, 55, tzinfo=datetime.timezone.utc,
            ),
        ),
        bot_info_version=None,
        restriction_reason=[],
        bot_inline_placeholder=None,
        lang_code=None,
        emoji_status=None,
        usernames=[],
        stories_max_id=None,
        color=None,
        profile_color=None,
        bot_active_users=None,
        bot_verification_icon=None,
        send_paid_messages_stars=None,
)


def _build_buttons_from_reply_markup(message: Message, client: TelegramClient, bot: User):
    keyboard = []

    for keyboard_row in message.reply_markup.rows:
        new_row = []
        for btn in keyboard_row.buttons:
            new_row.append(
                MessageButton(client, btn, object, bot, message.id)
            )

        keyboard.append(new_row)

    flat = [btn for row in keyboard for btn in row]

    return keyboard, flat, len(flat)


@pytest.fixture
def message_with_inline_keyboard(mock_client, fake_botfather_user) -> Message:
    m = Message(
        id=4444,
        peer_id=PeerUser(user_id=fake_botfather_user.id),
        date=datetime.datetime(
            2025, 1, 2, 3, 4, 55, tzinfo=datetime.timezone.utc,
        ),
        message="Message with an Inline Keyboard",
        out=False,
        mentioned=False,
        media_unread=False,
        silent=False,
        post=False,
        from_scheduled=False,
        legacy=False,
        edit_hide=False,
        pinned=False,
        noforwards=False,
        invert_media=False,
        offline=False,
        video_processing_pending=False,
        paid_suggested_post_stars=False,
        paid_suggested_post_ton=False,
        from_id=None,
        from_boosts_applied=None,
        saved_peer_id=None,
        fwd_from=None,
        via_bot_id=None,
        via_business_bot_id=None,
        reply_to=None,
        media=None,
        reply_markup=ReplyInlineMarkup(
            rows=[
                KeyboardButtonRow(
                    buttons=[
                        KeyboardButtonCallback(
                            text="Button 1",
                            data=b"callback_data_1",
                            requires_password=False,
                        ),
                        KeyboardButtonCallback(
                            text="Button with long text",
                            data=b"callback_data_2",
                            requires_password=False,
                        ),
                        KeyboardButtonCallback(
                            text="Button 3",
                            data=b"callback_data_3",
                            requires_password=False,
                        ),
                    ],
                ),
            ],
        ),
        entities=[],
        views=None,
        forwards=None,
        replies=None,
        edit_date=None,
        post_author=None,
        grouped_id=None,
        reactions=None,
        restriction_reason=[],
        ttl_period=None,
        quick_reply_shortcut_id=None,
        effect=None,
        factcheck=None,
        report_delivery_until_date=None,
        paid_message_stars=None,
        suggested_post=None,
    )

    m._buttons, m._buttons_flat, m._buttons_count = _build_buttons_from_reply_markup(
        m, mock_client, fake_botfather_user)

    return m


@pytest.fixture
def message_with_reply_keyboard(mock_client, fake_botfather_user):
    m =  Message(
        id=5555,
        peer_id=PeerUser(user_id=fake_botfather_user.id),
        date=datetime.datetime(
            2025, 1, 2, 3, 4, 55, tzinfo=datetime.timezone.utc,
        ),
        message="Test message with a Reply keyboard",
        out=False,
        mentioned=False,
        media_unread=False,
        silent=False,
        post=False,
        from_scheduled=False,
        legacy=False,
        edit_hide=False,
        pinned=False,
        noforwards=False,
        invert_media=False,
        offline=False,
        video_processing_pending=False,
        paid_suggested_post_stars=False,
        paid_suggested_post_ton=False,
        from_id=None,
        from_boosts_applied=None,
        saved_peer_id=None,
        fwd_from=None,
        via_bot_id=None,
        via_business_bot_id=None,
        reply_to=None,
        media=None,
        reply_markup=ReplyKeyboardMarkup(
            rows=[
                KeyboardButtonRow(
                    buttons=[
                        KeyboardButton(text="Button 1"),
                        KeyboardButton(text="Button 2"),
                    ],
                ),
            ],
            resize=True,
            single_use=False,
            selective=False,
            persistent=False,
            placeholder=None,
        ),
        entities=[],
        views=None,
        forwards=None,
        replies=None,
        edit_date=None,
        post_author=None,
        grouped_id=None,
        reactions=None,
        restriction_reason=[],
        ttl_period=None,
        quick_reply_shortcut_id=None,
        effect=None,
        factcheck=None,
        report_delivery_until_date=None,
        paid_message_stars=None,
        suggested_post=None,
    )

    m._buttons, m._buttons_flat, m._buttons_count = _build_buttons_from_reply_markup(
        m, mock_client, fake_botfather_user)

    return m


@pytest.fixture
async def controller(client, test_bot_username) -> AsyncGenerator[BotController, None]:
    controller = BotController(client, test_bot_username)
    await controller.start()
    yield controller
    await controller.stop()


@pytest.fixture
def mock_controller(mock_client, fake_botfather_user) -> BotController:
    controller = BotController(mock_client, fake_botfather_user.username)
    controller.target_username = fake_botfather_user.username
    controller._target_peer = fake_botfather_user
    controller._dispatcher_task = object

    controller.client.is_connected.return_value = True

    return controller
