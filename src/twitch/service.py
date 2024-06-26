from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import Logger

import hashlib
import hmac
from http import HTTPStatus
import json
from typing import List

from src.common.api_interfaces import APIInterfaces
from src.common.commands import resolve_command
from src.common.state_models import (
    Permission,
    State,
)
from src.twitch.interface import TwitchInterface
from src.twitch.models import (
    TwitchChallengeEvent,
    TwitchEventType,
    TwitchHeaders,
    TwitchNotificationEvent,
    TwitchRevocationEvent,
)
from src.twitch.notification_models import (
    TwitchChannelChatMessage,
    TwitchStreamOffline,
    TwitchStreamOnline,
)


logger = Logger(service="bryti")


class TwitchSignatureMismatchError(Exception):
    pass


class TwitchService:
    def __init__(
        self,
        api_interfaces: APIInterfaces,
        user_id: str,
        command_prefix: str,
        assignee_ids: List[str],
    ):
        self.api_interfaces = api_interfaces
        self.user_id = user_id
        self.command_prefix = f"!{command_prefix}"
        self.assignee_ids = assignee_ids

    def handle_event(self, headers: TwitchHeaders, body: str) -> Response:
        """
        Router for how to handle the event based on the event type.
        """
        logger.info("Received Twitch event", headers=headers.model_dump())
        self.verify_signature(headers, body)

        match headers.event_type:
            case TwitchEventType.CHALLENGE:
                return self.handle_challenge(body)
            case TwitchEventType.NOTIFICATION:
                return self.handle_notification(body)
            case TwitchEventType.REVOCATION:
                return self.handle_revocation(body)

    def verify_signature(self, headers: TwitchHeaders, body: str):
        """
        Validate the authenticity of the event (originated from Twitch) using the provided signature.
        """
        secret_str = f"bryti.{headers.subscription_type}.{headers.subscription_version}"
        secret = secret_str.encode("UTF-8")
        message = f"{headers.event_id}{headers.timestamp}{body}".encode("UTF-8")
        digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
        signature = f"sha256={digest}"
        if not hmac.compare_digest(signature, headers.signature):
            raise TwitchSignatureMismatchError

    def handle_challenge(self, body: str) -> Response:
        """
        Handle a callback verification challenge event by replying with the given challenge.
        """
        event = TwitchChallengeEvent.model_validate_json(body)
        logger.info("Handling challenge", event=event.model_dump())

        challenge = event.challenge
        return Response(
            status_code=HTTPStatus.OK,
            content_type=content_types.TEXT_PLAIN,
            body=challenge,
        )

    def handle_notification(self, body: str) -> Response:
        """
        Router for how to handle the subscription notification event based on the subscription event type.
        """
        event = TwitchNotificationEvent.model_validate_json(body)
        logger.info("Handling notification", event=event.model_dump())
        match event.event:
            case TwitchChannelChatMessage(chatter_user_id=chatter_user_id):
                if chatter_user_id != self.user_id:
                    self.handle_chat_message(event.event)
            case TwitchStreamOnline() | TwitchStreamOffline():
                self.handle_stream_event(event.event)

        # Acknowledge notification.
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body="{}",
        )

    def handle_chat_message(self, event: TwitchChannelChatMessage):
        """
        Handle a chat message event by, if the message is a command invocation, attempting to execute it.
        """
        # Check if it matches the configured command prefix.
        split_msg = event.message.text.lower().strip().split()
        if len(split_msg) == 0 or split_msg[0] != self.command_prefix:
            return

        logger.info("Resolving command", command_args=split_msg[1:])
        CommandClass, args = resolve_command(split_msg[1:])
        if CommandClass:
            can_invoke, state, permission = self.retrieve_event_context(event)
            logger.info(
                "Retrieved event context",
                can_invoke=can_invoke,
                state=state,
                permission=permission,
            )
            if not can_invoke:
                return

            logger.info(
                "Executing command",
                command=CommandClass,
                command_args=args,
            )
            try:
                reply = CommandClass(
                    self.api_interfaces,
                    state,
                    permission,
                ).execute(*args)
            except TypeError as e:
                reply = "Invalid call to command!"
        else:
            reply = "Couldn't find that command!"

        logger.info("Replying to message", reply=reply)
        self.api_interfaces.twitch.send_chat_message(
            event.broadcaster_user_id,
            self.user_id,
            reply,
            reply_message_id=event.message_id,
        )

    def retrieve_event_context(
        self,
        event: TwitchChannelChatMessage,
    ) -> (bool, State, Permission):
        """
        Look up user information/state from the state table.
        """

        # Get broadcaster state (or default if does not exist yet).
        broadcaster = self.api_interfaces.state_table.lookup_by_twitch(
            event.broadcaster_user_id
        )
        if broadcaster is not None:
            state = self.api_interfaces.state_table.get_state(broadcaster.user)
        else:
            state = State(
                user=event.broadcaster_user_login,
                twitch_user_id=event.broadcaster_user_id,
            )

        chatter = self.api_interfaces.state_table.lookup_by_twitch(
            event.chatter_user_id
        )

        # If there are no assignees (in prod) or if the chatter is assigned to the PR (in dev).
        can_invoke = self.assignee_ids is None or (
            chatter is not None and chatter.github_user_id in self.assignee_ids
        )

        # If the broadcaster called the command, otherwise if they have permissions given by the broadcaster.
        permission = Permission.EVERYBODY
        if event.broadcaster_user_id == event.chatter_user_id:
            permission = Permission.BROADCASTER
        elif chatter is not None and chatter.user in state.members:
            permission = state.members[chatter.user]

        return can_invoke, state, permission

    def handle_stream_event(self, event: TwitchStreamOnline | TwitchStreamOffline):
        pass

    def handle_revocation(self, body: str) -> Response:
        """
        Handle a subscription revocation event.
        """
        event = TwitchRevocationEvent.model_validate_json(body)
        logger.info("Handling revocation", event=event.model_dump())

        # TODO: send Discord notification.

        # Acknowledge revocation.
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body="{}",
        )
