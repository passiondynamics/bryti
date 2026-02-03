from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from pydantic import ValidationError

from http import HTTPStatus
from typing import (
    Any,
    Dict,
)

from src.common.api_interfaces import APIInterfaces
from src.common.state_table_interface import StateTableInterface
from src.config import load_env_vars
from src.discord.models import DiscordHeaders
from src.discord.service import (
    DiscordService,
    DiscordSignatureMismatchError,
)
from src.twitch.interface import TwitchInterface
from src.twitch.models import TwitchHeaders
from src.twitch.service import (
    TwitchService,
    TwitchSignatureMismatchError,
)


# --- Global/cold start variables ---

logger = Logger(service="bryti")
app = APIGatewayHttpResolver()

env_vars = load_env_vars()
ENV = env_vars["ENV"]
STATE_TABLE_NAME = f"bryti-{ENV}-state"
COMMAND_PREFIX = "bryti" if ENV == "prod" else f"bryti-{ENV}"

dynamodb_client = boto3.client("dynamodb")
state_table_interface = StateTableInterface(
    dynamodb_client,
    STATE_TABLE_NAME,
)
twitch_interface = TwitchInterface(
    env_vars["TWITCH_CLIENT_ID"],
    env_vars["TWITCH_CLIENT_SECRET"],
)
api_interfaces = APIInterfaces(
    state_table_interface,
    twitch_interface,
)

# TODO: construct Discord interface and pass to services.
twitch_service = TwitchService(
    api_interfaces,
    env_vars["TWITCH_USER_ID"],
    COMMAND_PREFIX,
    env_vars["GITHUB_ASSIGNEE_IDS"],
)

discord_service = DiscordService(
    # api_interfaces,
    env_vars["DISCORD_APP_PUBLIC_KEY"],
    # COMMAND_PREFIX,
    # env_vars["GITHUB_ASSIGNEE_IDS"],
)


# --- Main logic ---


class UnknownEventSourceError(Exception):
    pass


@app.post("/bryti")
def bryti_handler() -> Response:
    # Determine event source by request headers.
    headers = app.current_event.headers
    try:
        twitch_headers = TwitchHeaders.model_validate(headers)
        return twitch_service.handle_event(
            twitch_headers,
            app.current_event.decoded_body,
        )
    except ValidationError:
        pass

    try:
        discord_headers = DiscordHeaders.model_validate(headers)
        return discord_service.handle_event(
            discord_headers,
            app.current_event.decoded_body,
        )
    except ValidationError:
        pass

    # If no matching event source found, raise an error.
    raise UnknownEventSourceError


@app.exception_handler(UnknownEventSourceError)
def unknown_event_source(e: UnknownEventSourceError) -> Response:
    logger.exception(e)
    return Response(
        status_code=HTTPStatus.UNAUTHORIZED,
        content_type=content_types.APPLICATION_JSON,
        body="{}",
    )


@app.exception_handler([TwitchSignatureMismatchError, DiscordSignatureMismatchError])
def on_signature_mismatch(
    e: TwitchSignatureMismatchError | DiscordSignatureMismatchError,
) -> Response:
    logger.exception(e)
    return Response(
        status_code=HTTPStatus.FORBIDDEN,
        content_type=content_types.APPLICATION_JSON,
        body="{}",
    )


@logger.inject_lambda_context()
def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info("Lambda triggered", event=event, context=context)
    response = app.resolve(event, context)
    logger.info("Returning response", response=response)
    return response
