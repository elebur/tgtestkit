"""Entry point to TgTestKit features."""
import asyncio
import logging
from collections.abc import AsyncGenerator, Iterable, Sequence
from contextlib import asynccontextmanager
from time import time

from telethon import TelegramClient
from telethon.events import MessageEdited, NewMessage
from telethon.hints import EntityLike
from telethon.tl.custom.inlineresult import InlineResult
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import messages
from telethon.types import BotCommand, GeoPoint, Message, User

from tgtestkit.collector import collect
from tgtestkit.containers.responses import Response
from tgtestkit.expectation import Expectation
from tgtestkit.timeout_settings import TimeoutSettings
from tgtestkit.utils.frame_utils import get_caller_function_name
from tgtestkit.utils.sentinel import NotSet

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING,
)


class BotController:
    """
    This class is the entry point for all interactions.

    It can be used to interact with either regular bots
    or userbots in `TgIntegration`. It expects a Telethon `TelegramClient`
    (typically a **user client**) that serves as the controll**ing** account for a
    specific `peer` - which can be seen as the "bot under test" or
    "conversation partner".
    In addition, the controller holds a number of settings
    to control the timeouts for all these interactions.
    """

    def __init__(
        self,
        client: TelegramClient,
        target_username: EntityLike,
        *,
        max_wait: float = 20.0,
        raise_no_response: bool = True,
        global_action_delay: float = 0.8,
    ) -> None:
        """
        Create a new `BotController`.

        Args:
            client (TelegramClient): A telethon user client that acts
                as the controll*ing* account.
            target_username (EntityLike): The username or an ID of a bot under the test or
                a conversation partner.
            max_wait (float, optional): Maximum time in seconds for the `peer`
                to produce the expected response. Defaults to 20.0.
            wait_consecutive (float | None, optional): Additional time in seconds
                to wait for _additional_ messages upon receiving a response
                (even when `max_wait` is exceeded). Defaults to 2.0.
            raise_no_response (bool, optional): _description_Whether to raise
                an exception on timeout/invalid response or to log silently.
                Defaults to True.
            global_action_delay (float, optional): The time to wait in between
                `collect` calls. Defaults to 0.8.
        """
        self.client = client
        self.target_username = target_username
        self.max_wait_response = max_wait
        self.raise_no_response = raise_no_response
        self.global_action_delay = global_action_delay

        self._target_peer: User | None = None
        self._me: User | None = None
        self._last_response_ts: float | None = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self._dispatcher_task: asyncio.Task | None = None

    async def start(self, *, start_client: bool = True) -> None:
        """
        Fetch and cache information about the given `peer`, start updates dispatching.

        And optionally starts the assigned `client`.
        This method will automatically be called when coroutines of this class
        are invoked, but you can call it manually to override defaults
        (namely whether to `start_client`).

        !!! note
            It is unlikely that you will need to call this manually.

        Args:
            start_client (bool, optional): Set to `False` if the client should
                not be started as part of initialization. Defaults to True.
        """
        if start_client and not self.client.is_connected():
            self.logger.debug("Starting the TelegramClient")
            await self.client.connect()
            self._me = await self.client.get_me()

        if not self._target_peer:
            self._target_peer = await self.client.get_entity(self.target_username)

        if self.client.is_connected() and not self._dispatcher_task:
            self.logger.debug("Starting the Dispatcher")
            self._dispatcher_task = asyncio.create_task(
                self.client._run_until_disconnected(),  # noqa: SLF001
            )

    async def stop(self) -> None:
        """Disconnect the client and stop fetching updates."""
        self.logger.debug("Disconnecting the client.")
        await self.client.disconnect()
        self._dispatcher_task = None

    async def _ensure_preconditions(
        self,
        *,
        bots_only: bool = False,
        peer: EntityLike | None = None,
    ) -> None:
        """
        Check that the controller is properly started.

        Args:
            bots_only (bool, optional): True if the `peer` must be a bot.
                Defaults to False.
            peer (EntityLike, optional): a peer to check to be a bot (if `bots_only`
                is True). If `None` then the controller's 'target_peer' will be checked.
                Defaults to None.

        Raises:
            ValueError: if the peer is not a bot.
            TypeError: if the peer is not of type User.
        """
        if (
            not self.client.is_connected()
            or not self._dispatcher_task
            or not self._target_peer
        ):
            await self.start()

        if peer:
            input_peer = await self.client.get_entity(peer)
        else:
            input_peer = self._target_peer

        if bots_only and not isinstance(input_peer, User):
            msg = (
                "'peer' must an instance of `telethon.tl.types.User`. "
                f"Got {type(input_peer)} instead."
            )
            raise TypeError(msg)

        if bots_only and not input_peer.bot:
            caller = get_caller_function_name()
            msg = (
                f"The '{caller}' expects the peer to be a bot, "
                f"but '{input_peer.username or input_peer.id}' is not a bot."
            )
            raise ValueError(msg)

    async def get_commands_list(
        self,
        target_bot: EntityLike | None = None,
    ) -> list[BotCommand]:
        """
        Get the bot's registered commands.

        Args:
            target_bot (EntityLike, optional): the bot to get commands for.
                If not set then `BotController.target_peer` will be used.
                Defaults to None.

        Returns:
            list[BotCommand]:
        """
        self.logger.debug("Getting the commands list")
        await self._ensure_preconditions(bots_only=True, peer=target_bot)

        peer = target_bot or self._target_peer
        bot_user_info = await self.client(GetFullUserRequest(peer))

        return bot_user_info.full_user.bot_info.commands

    async def delete_messages(
        self,
        *,
        just_clear: bool = False,
        revoke: bool = True,
    ) -> messages.AffectedHistory:
        """
        Delete the 100 oldest messages in the chat with the assigned `peer`.

        https://core.telegram.org/method/messages.deleteHistory

        !!! warning
            Be careful as this will completely drop your mutual message history.

        Args:
            just_clear (bool, optional): Just clear history for the current user,
                without actually removing messages for every chat user.
                Defaults to True.
            revoke (bool, optional): Whether to delete the message history
                for all chat participants.
                Defaults to True.
        Returns:
            `telethon.tl.types.messages.AffectedHistory`:
        """
        async with self.client:
            await self._ensure_preconditions()

            return await self.client(
                DeleteHistoryRequest(
                    peer=self._target_peer,
                    max_id=0,
                    just_clear=just_clear,
                    revoke=revoke,
                    min_date=None,
                    max_date=None,
                ),
            )

    @asynccontextmanager
    async def collect_messages(  # noqa: PLR0913
        self,
        count: int = 0,
        *,
        max_wait: float = 15,
        wait_consecutive: float = 2.0,
        additional_peers: tuple[EntityLike] | list[EntityLike] | None = None,
        incoming: bool = True,
        outgoing: bool = False,
        new_messages: bool = True,
        edited_messages: bool = True,
        unhandled_updates: bool = False,
        raise_: bool | None = None,
    ) -> AsyncGenerator[Response]:
        """
        Use as a context manager to gather updates with respect to `custom_filters`.

        Args:
            count (int, optional): number of updates the controller must receive.
            max_wait (float, optional): the maximum duration in seconds to receive all
                the expected updates. Defaults to 15.
            wait_consecutive (float): Additional time in seconds
                to wait for _additional_ messages upon receiving a response
                (even when `max_wait` is exceeded). Defaults to 2.0.
            additional_peers (list[EntityLike], optional): peers to collect updates
                from. May be an ID, a username, a Telethon's `Entity`, etc.
                Defaults to None.
            incoming (bool, optional):
                If set to `True`, only **incoming** messages will be handled.
                Mutually exclusive with ``outgoing`` (can only set one of either).
            outgoing (bool, optional):
                If set to `True`, only **outgoing** messages will be handled.
                Mutually exclusive with ``incoming`` (can only set one of either).
                See a warning in the Telethon's documentation:
                https://docs.telethon.dev/en/stable/modules/events.html#telethon.events.messageedited.MessageEdited
            new_messages (bool): collect new messages.
            edited_messages (bool): collect edited messages.
            unhandled_updates (bool): collect all updates that were not by
                other handlers.
            raise_ (bool, optional): whether to raise an exception if didn't get
                `count` updates during `max_wait` seconds. If not set, then
                `BotController.raise_no_response` will be used. Defaults to None.

        Yields:
            AsyncGenerator[Response]:
        """
        if not any((new_messages, edited_messages, unhandled_updates)):
            msg = (
                "One of (or all) of 'new_messages', 'edited_messages' or "
                "'unhandled_updates' must be set to `True`"
            )
            raise ValueError(msg)

        await self._ensure_preconditions()
        await self._wait_if_necessary()

        peers = [self._target_peer.id]
        if additional_peers:
            if (isinstance(additional_peers, str) or
                not isinstance(additional_peers, Sequence)
            ):
                msg = (
                    "`additional_peers` must be a list or a tuple. "
                    f"Got '{type(additional_peers)}' instead."
                )
                raise TypeError(msg)
            peers.extend(additional_peers)

        handlers = []
        if new_messages:
            handlers.append(
                NewMessage(
                    chats=peers,
                    incoming=incoming,
                    outgoing=outgoing,
                ),
            )

        if edited_messages:
            handlers.append(
                MessageEdited(
                    chats=peers,
                    incoming=incoming,
                    outgoing=outgoing,
                ),
            )

        async with collect(
            self,
            handlers=handlers,
            unhandled_updates=True,
            expectation=Expectation(
                min_updates=count or NotSet,
                max_updates=count or NotSet,
            ),
            timeouts=TimeoutSettings(
                max_wait=max_wait,
                wait_consecutive=wait_consecutive,
                raise_on_timeout=raise_
                if raise_ is not None else self.raise_no_response,
            ),
        ) as response:
            yield response

        self._last_response_ts = response.last_message_timestamp

    async def _wait_if_necessary(self) -> None:
        if not self.global_action_delay or not self._last_response_ts:
            return

        wait_for = (self.global_action_delay + self._last_response_ts) - time()
        if wait_for > 0:
            self.logger.debug(
                f"Waiting {wait_for} seconds to respect global action delay..."
            )
            await asyncio.sleep(wait_for)

    async def send_command(
        self,
        command: str,
        args: Iterable[str] | str | None = None,
        peer: EntityLike | None = None,
        *,
        add_bot_name: bool = False,
    ) -> Message:
        """
        Send a slash-command with corresponding arguments.

        Args:
            command (str): a command to be sent (e.g. '/start')
            args (Iterable[str] | None, optional): arguments that must be sent
                with the command. If the 'args' is `str` then it is appended as is,
                if it is an Iterable, then items will be joined with a space as a
                separator.
                Defaults to None.
            peer (EntityLike, optional): a bot who receives the command.
                Defaults to None.
            add_bot_name (bool, optional): whether to add a bot's name after
                the command ('/command@BotName'). Defaults to False.

        Returns:
            telethon.types.Message:
        """
        await self._ensure_preconditions()

        text = "/" + command.removeprefix("/")

        if add_bot_name and self._target_peer.username:
            text += f"@{self._target_peer.username}"

        if args:
            text += f" {args}" if isinstance(args, str) else f" {' '.join(args)}"

        target_peer = self._target_peer
        if peer:
            target_peer = await self.client.get_entity(peer)

        return await self.client.send_message(target_peer, text)

    async def query_inline(
        self,
        query: str,
        peer: EntityLike | None = None,
        offset: str = "20",
        limit: int = 20,
        geo_point: GeoPoint | None = None,
    ) -> list[InlineResult]:
        """
        Request inline results from the `peer` (which needs to be a bot).

        Args:
            query (str): The query text.
            peer (EntityLike, optional): a bot to request inline queries from.
                Defaults to None.
            offset (`str`, optional):
                The string offset to use for the bot.
            limit (int, optional): a number of queries to be returned. Defaults to 20.
            geo_point (`GeoPoint`, optional)
                The geo point location information to send to the bot
                for localized results. Available under some bots.
        Raises:
            ValueError: if the `limit` is less or equal to zero.

        Returns:
            A list of `telethon.tl.custom.inlineresult.InlineResult`s.
        """
        target_peer = self._target_peer
        if peer:
            target_peer = await self.client.get_entity(peer)

        await self._ensure_preconditions(bots_only=True, peer=target_peer)

        if limit <= 0:
            msg = "'limit' can not be less or equal to 0"
            raise ValueError(msg)

        result = []
        while len(result) < limit:
            queries = await self.client.inline_query(
                bot=target_peer,
                query=query,
                entity=self._me,
                offset=offset,
                geo_point=geo_point,
            )
            result.extend(queries)
            if queries.next_offset is None:
                break

        return result[:limit]
