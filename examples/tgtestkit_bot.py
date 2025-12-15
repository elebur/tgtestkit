import asyncio

from telethon import TelegramClient
from telethon.events import CallbackQuery, NewMessage
from telethon.tl.custom.button import Button

API_ID = 1234
API_HASH = ""
BOT_ACCESS_TOKEN = ""

client = TelegramClient(
    session="bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
)


@client.on(NewMessage(pattern="^/start"))
async def start(event: NewMessage):
    """
    This the response to the /start command.

    The bot will send three messages, each contains ReplyKeyboard.
    """

    chat = await event.get_chat()

    await event.message.respond(
        f"Hello, {chat.username}",
        buttons=[[Button.text("Button 1", resize=True)]],
    )

    await asyncio.sleep(0.3)

    await event.message.respond(
        "This is the 2nd message for the /start command.",
        buttons=[[
            Button.text("Button 1", resize=True),
            Button.text("Button 2", resize=True),
            Button.text("Button 3", resize=True),
        ]],
    )

    await asyncio.sleep(0.2)

    await event.message.respond(
        "This is the message with a final reply keyboard",
        buttons=[[
            Button.text("Show the Inline Keyboard", resize=True),
            Button.text("Hello", resize=True),
        ]],
    )


@client.on(NewMessage(pattern="^/cancel"))
async def cancel(event: NewMessage):

    await event.message.respond(
        "You have requested the cancel command.",
    )


@client.on(NewMessage(pattern=r"^Show the Inline Keyboard$"))
async def inline_keyboard(event: NewMessage):
    """Example of a message with InlineKeyboard."""

    await event.message.respond("Let's explore inline buttons...")
    await asyncio.sleep(0.7)
    await event.message.respond(
        "...and here we have some.",
        buttons=[[
            Button.inline("Button 1", b"button_1"),
            Button.inline("Button 2", b"callback_data_2"),
            Button.inline("Button 3", b"callback_data_3"),
        ]],
    )


@client.on(CallbackQuery(pattern=r"^button_1$"))
async def button1_callback(event: CallbackQuery):
    await event.edit("Hm, it seems you have pressed the inline 'Button 1'")


@client.on(CallbackQuery(pattern=r"^callback_data_\d$"))
async def inline_button_clicked(event: CallbackQuery):
    """The callback for the inline buttons."""
    button_number = event.data.decode("utf-8")[-1]

    alert = False
    if button_number == "2":
        alert = True
    await event.answer(f"Button #{button_number}", alert=alert)
    await event.respond(
        f"The inline button #{button_number} was clicked.",
    )


def main():
    with client:
        client.start(BOT_ACCESS_TOKEN)
        client.run_until_disconnected()

if __name__ == "__main__":
    main()
