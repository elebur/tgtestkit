TgTestKit
=============

<ins>An integration test and automation library for [Telegram Bots](https://core.telegram.org/bots) based on [Telethon](https://github.com/LonamiWebs/Telethon).</ins>
<br />**Test your bot in realtime scenarios!**


> [!NOTE]
> The origin of the TgTestKit is [TgIntegration](https://github.com/JosXa/tgintegration)
>
> The [link to the commit](https://github.com/JosXa/tgintegration/tree/39dfc82eb5c80bb6845c12edf0c112e2fa7de26f) TgTestKit was forked from.

<!-- TODO: add badges -->
<!-- [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tgintegration)](https://pypi.org/project/tgintegration/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tgintegration)](https://pypi.org/project/tgintegration/)
[![PyPI](https://img.shields.io/pypi/v/tgintegration)](https://pypi.org/project/tgintegration/)
![GitHub top language](https://img.shields.io/github/languages/top/josxa/tgintegration)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/josxa/tgintegration/Build/master)](https://github.com/JosXa/tgintegration/actions?query=workflow%3ABuild)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/josxa/tgintegration/Docs?label=docs)](https://josxa.github.io/tgintegration) -->

---

[Features](#features) • [Requirements](#prerequisites) • [Installation](#installation) • [**Quick Start Guide**](#quick-start-guide)
 <!-- • [Test Frameworks](#integrating-with-test-frameworks) -->

<!-- TODO: - 📖 [Documentation](https://josxa.github.io/tgintegration/) -->
<!-- TODO: - 👥 [Telegram Chat](https://t.me/TgIntegration) -->

Features
--------

<!-- TODO: ▶️ [**See it in action!** 🎬](https://josxa.github.io/tgintegration/#see-it-in-action) -->

- 👤 Log into a Telegram user account and interact with bots or other users
- ✅ Write **realtime integration tests** to ensure that your bot works as expected!
- ⚡️ **Automate any interaction** on Telegram!
- 🛡 Fully typed for safety and **autocompletion** with your favorite IDE
- 🐍 Built for modern Python (3.10+) with high test coverage
 <!-- TODO: ▶️ [Pytest examples](https://github.com/JosXa/tgintegration/tree/master/examples/pytest) -->
 <!-- TODO: ▶️ [Automatically play @IdleTownBot](https://github.com/JosXa/tgintegration/blob/master/examples/automation/idletown.py) | [More examples](https://github.com/JosXa/tgintegration/tree/master/examples/automation) -->


Prerequisites
-------------

[Same as Telethon](https://docs.telethon.dev/en/stable/basic/signing-in.html#signing-in):

- A [Telegram API key](https://my.telegram.org/).
- [A user session](https://docs.telethon.dev/en/stable/basic/signing-in.html#id2) (seeing things happen in your own account is great for getting started)
- But: **Python 3.10** or higher!

```python
from telethon import TelegramClient

# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
api_id = 12345
api_hash = '0123456789abcdef0123456789abcdef'

client = TelegramClient('session_name', api_id, api_hash)
client.start()
```

A basic understanding of async/await and [asynchronous context managers](https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager) is assumed, as TgIntegration heavily relies on the latter to automate conversations.


Installation
------------

<!-- TODO: link to the latest release. Is it even possible? -->
```pip install git+https://github.com/elebur/tgtestkit.git```


Quick Start Guide
-----------------
#### Setup

To follow this guide you have to run [the test bot](https://github.com/elebur/tgtestkit/blob/main/examples/tgtestkit_bot.py)

> [!NOTE]
> Requirements are the same as [described above](#prerequisites) and you would
also need [a bot token](https://core.telegram.org/bots)

After [configuring a Telethon **user client**](https://docs.telethon.dev/en/stable/basic/signing-in.html#id2),
let's start by creating a `BotController`:

``` python
from telethon import TelegramClient

from tgtestkit import BotController

BOT_USERNAME = ""   # A username of the bot under the test.
API_ID = 1234       # Telegram API ID.
API_HASH = ""       # Telegram API hash.

client = TelegramClient(
    session="test_account",  # this value will be used as a file name for a session file.
    api_hash=API_HASH,
    api_id=API_ID,
)

controller = BotController(
    client=client,                   # This assumes you already have a Pyrogram user client available
    target_username=BOT_USERNAME,    # The @username of the bot under test
    max_wait=8,                      # Maximum timeout for responses (optional)
    raise_no_response=True,          # Raise `InvalidResponseError` when no response is received (defaults to True)
    global_action_delay=2.5,         # Choosing a rather high delay so we can observe what's happening (optional)
)


```

Let's clear chat history
> [!WARNING]
> This action will delete all chat history.
```python
# You might need to call this method multiple times to clear the whole history,
# because it deletes only 100 hundred messages per request.
await controller.delete_messages()  # Start with a blank screen (⚠️)
```

Now, let's send `/start` to the bot and wait until exactly three messages
have been received by using the asynchronous `collect_messages` context manager:

```python
async with controller.collect_messages(count=3, max_wait=4, raise_=False) as reply_keyboard_response:
    await controller.send_command("start")

assert reply_keyboard_response.has_messages         # Check that the `Response` has messages.
assert len(reply_keyboard_response.messages) == 3   # Ensure that exactly three messages were received, bundled under a `Response` object
```

Examining the buttons in the response...

```python
# The response has three `ReplyKeyboard`s,
# because each of the messages has its own keyboard.
assert len(reply_keyboard_response.get_reply_keyboards()) == 3
# But only the most recent ReplyKeyboard is shown in the Telegram UI,
# and this the keyboard that will be returned by the
# `Response.reply_keyboard` property.
assert reply_keyboard_response.reply_keyboard.buttons_count == 2
```

We can also press keyboard buttons, for example based on a regular expression:

``` python
reply_keyboard = reply_keyboard_response.reply_keyboard
async with controller.collect_messages(count=2, max_wait=4, raise_=False) as click_reply_resp:
    # Based on the regular expression.
    await reply_keyboard.click(pattern=r"Show the Inline Keyboard")
    # Based on the index.
    # await keyboard.click(index=0)
```

Clicking inline keyboards pretty much the same:
``` python
inline_keyboard = click_reply_resp.get_inline_keyboards()[-1]
async with controller.collect_messages(count=1, max_wait=4, raise_=False) as click_inline_resp:
    # Now let's click by index
    await inline_keyboard.click(index=0)
```

Let's ensure that we caught the edited message:
```python
assert click_inline_resp.messages[0].message == "Hm, it seems you have pressed the inline 'Button 1'"
```

Now let's click the reply keyboard button again.
```python
async with controller.collect_messages(count=2, max_wait=4, raise_=False) as click_reply_resp:
    response_reply = await reply_keyboard.click(pattern=r"Show the Inline Keyboard")
```

When the controller clicks the reply button then `click` method returns [`Message`](https://docs.telethon.dev/en/stable/quick-references/objects-reference.html#message) object
```python
from telethon.types import Message
assert isinstance(response_reply, Message)
```

After clicking an inline button `click` returns `BotCallbackAnswer` ([Telegram docs](https://core.telegram.org/constructor/messages.botCallbackAnswer). [Telethon docs](https://tl.telethon.dev/constructors/messages/bot_callback_answer.html))
```python
inline_keyboard = click_reply_resp.get_inline_keyboards()[-1]
async with controller.collect_messages(count=1, max_wait=4, raise_=False) as click_inline_resp:
    response_inline = await inline_keyboard.click(index=1)

from telethon.tl.types.messages import BotCallbackAnswer
assert isinstance(response_inline, BotCallbackAnswer)
```

#### Error handling

So what happens when the peer fails to respond?

The following instruction will raise an `ExpectationError` after `controller.max_wait` seconds.
This is because we passed `raise_no_response=True` during controller initialization.

``` python
from tgtestkit import ExpectationError
try:
    async with controller.collect_messages():
        await controller.send_command("ayylmao")
except ExpectationError:
    print("No response")
```

Let's explicitly set `raise_` to `False` so that no exception occurs:

``` python
async with controller.collect_messages(raise_=False) as response:
    # You can use the `TelegramClient` object directly.
    await client.send_message(controller.target_username, "Henlo Fren")
```

In this case, _tgtestkit_ will simply emit a warning, but you can still assert
that no response has been received by using the `has_messages` property:

``` python
assert not response.has_messages
```


<!-- Integrating with Test Frameworks
# TODO: create simple pytest examples for the example bot.
--------------------------------

### [pytest](https://docs.pytest.org/en/stable/index.html)

Pytest is the recommended test framework for use with _tgintegration_. You can
[browse through several examples](https://github.com/JosXa/tgintegration/tree/master/examples/pytest)
and _tgintegration_ also uses pytest for its own test suite.

### unittest

I haven't tried out the builtin `unittest` library in combination with _tgintegration_ yet,
but theoretically I don't see any problems with it.
If you do decide to try it, it would be awesome if you could tell me about your
experience and whether anything could be improved 🙂
Let us know at 👉 https://t.me/TgIntegration or in an issue. -->
