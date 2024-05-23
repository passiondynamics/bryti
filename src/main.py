from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from http import HTTPStatus
from typing import (
    Any,
    Dict,
)

from src.config import load_env_vars
from src.twitch.interface import TwitchInterface
from src.twitch.models import TwitchHeaders
from src.twitch.service import (
    TwitchService,
    TwitchSignatureMismatchError,
)


logger = Logger(service="bryti")
app = APIGatewayHttpResolver()
env_vars = load_env_vars()
twitch_interface = TwitchInterface(
    env_vars["TWITCH_CLIENT_ID"],
    env_vars["TWITCH_CLIENT_SECRET"],
)
# TODO: construct Discord + DynamoDB interfaces and pass to services.
twitch_service = TwitchService(
    twitch_interface,
    env_vars["TWITCH_USER_ID"],
    env_vars["COMMAND_PREFIX"],
)


class UnknownEventSourceError(Exception):
    pass


@app.post("/bryti")
def bryti_handler() -> Response:
    # Determine event source by request headers.
    try:
        twitch_headers = TwitchHeaders.model_validate(app.current_event.headers)
        return twitch_service.handle_event(
            twitch_headers,
            app.current_event.decoded_body,
        )
    except ValidationError:
        pass

    # TODO: implement Discord service.

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


@app.exception_handler(TwitchSignatureMismatchError)
def on_signature_mismatch(e: TwitchSignatureMismatchError) -> Response:
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
