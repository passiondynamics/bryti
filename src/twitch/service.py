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

from src.common.commands import (
    Permission,
    resolve_command,
)
from src.twitch.models import (
    TwitchChallengeEvent,
    TwitchEventType,
    TwitchHeaders,
    TwitchNotificationEvent,
    TwitchRevocationEvent,
)
from src.twitch.event_models import (
    TwitchChannelChatMessage,
    TwitchStreamOffline,
    TwitchStreamOnline,
)


logger = Logger(service="bryti")


class TwitchSignatureMismatchError(Exception):
    pass


class TwitchService:
    def __init__(self, command_prefix: str):
        self.command_prefix = f"!{command_prefix}"

    def handle_event(self, headers: TwitchHeaders, body: str) -> Response:
        """
        Router for how to handle the event based on the event type.
        """
        logger.info("Received Twitch event", headers=headers)
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
        Handle a callback verification challenge event.
        """
        event = TwitchChallengeEvent.model_validate_json(body)
        logger.info("Handling challenge", event=event)

        challenge = event.challenge
        return Response(
            status_code=HTTPStatus.OK,
            content_type=content_types.TEXT_PLAIN,
            body=challenge,
        )

    def handle_notification(self, body: str) -> Response:
        """
        Handle a subscription notification event.
        """
        event = TwitchNotificationEvent.model_validate_json(body)
        logger.info("Handling notification", event=event)
        match event.event:
            case TwitchChannelChatMessage(message=message):
                # Check if it's a command call, execute if so.
                split_msg = message.lower().split()
                if len(split_msg) > 0 and split_msg[0] == self.command_prefix:
                    CommandClass, args = resolve_command(split_msg[1:])
                    if not CommandClass:
                        # TODO: determine permission by chatting user info.
                        output = CommandClass(None, Permission.EVERYBODY).execute(*args)
            case TwitchStreamOnline() | TwitchStreamOffline():
                # TODO: notify Discord.
                pass

        # Acknowledge notification.
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body="{}",
        )

    def handle_revocation(self, body: str) -> Response:
        """
        Handle a subscription revocation event.
        """
        event = TwitchRevocationEvent.model_validate_json(body)
        logger.info("Handling revocation", event=event)

        # TODO: send Discord notification.

        # Acknowledge revocation.
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body="{}",
        )
