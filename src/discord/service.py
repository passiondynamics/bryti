from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.event_handler import Response
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import ValidationError

from src.discord.models import (
    DiscordHeaders,
    DiscordEvent,
    DiscordEventType,
)

logger = Logger(service="bryti")


class DiscordSignatureMismatchError(BadSignatureError):
    pass


class DiscordService:
    def __init__(
        self,
        # api_interfaces: APIInterfaces,
        # user_id: str,
        discord_app_public_key: str,
        # command_prefix: str,
        # assignee_ids: List[str],
    ):
        # self.api_interfaces = api_interfaces
        # self.user_id = user_id
        self.discord_app_public_key = discord_app_public_key

    # self.command_prefix = f"!{command_prefix}"
    # self.assignee_ids = assignee_ids

    def handle_event(self, headers: DiscordHeaders, body: str) -> Response:
        """
        Router for how to handle the event based on the event type.
        """
        logger.info("Received Discord event", headers=headers.model_dump())
        self.verify_signature(headers, body)
        try:
            event = DiscordEvent.model_validate(body)
        except ValidationError:
            pass

        logger.info("DEBUGGING:", body)
        event = DiscordEvent.model_validate_json(body)
        match event.event_type:
            case DiscordEventType.PING:
                return self.handle_ping(event)
            case DiscordEventType.APPLICATION_COMMAND:
                return self.handle_command(event)

    def verify_signature(self, headers: DiscordHeaders, body: str):
        """
        Validate the authenticity of the event (originated from Discord) using the provided signature.
        """
        verify_key = VerifyKey(bytes.fromhex(self.discord_app_public_key))
        message = f"{headers.timestamp}{body}".encode()
        signature_bytes = bytes.fromhex(headers.signature)
        try:
            verify_key.verify(message, signature_bytes)
        except BadSignatureError as e:
            raise DiscordSignatureMismatchError from e

    def handle_ping(self, event: DiscordEvent) -> Response:
        """
        Handle a callback verification ping event with a pong reply.
        """
        logger.info("Handling ping", event=event.model_dump())

        return Response(
            status_code=HTTPStatus.OK,
            content_type=content_types.APPLICATION_JSON,
            body='{"type": 1}',
        )

    def handle_command(self, event: DiscordEvent) -> Response:
        """
        Handle a command invocation by attempting to execute it.
        """
        logger.info("Handling application command", event=event.model_dump())
