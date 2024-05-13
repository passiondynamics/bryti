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
from src.twitch.models import TwitchHeaders
from src.twitch.service import TwitchService


logger = Logger(service="bryti")
app = APIGatewayHttpResolver()
env_vars = load_env_vars()
twitch_service = TwitchService()


@app.get("/bryti")
def bryti_handler() -> Response:
    # Determine event source by request headers.
    try:
        twitch_headers = TwitchHeaders.model_validate(app.current_event.headers)
        return twitch_service.handle_event(
            twitch_headers.event_type,
            app.current_event.decoded_body,
        )
    except ValidationError:
        pass

    # If no matching event source found, hand back a default response.
    return Response(
        status_code=HTTPStatus.NO_CONTENT,
        content_type=content_types.APPLICATION_JSON,
        body="{}",
    )


@logger.inject_lambda_context()
def lambda_handler(event: Dict[str, Any], context: LambdaContext):
    logger.info("Lambda triggered", event=event, context=context)
    return app.resolve(event, context)
