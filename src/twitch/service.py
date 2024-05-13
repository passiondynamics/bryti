from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import Logger

from http import HTTPStatus
import json

from src.twitch.models import (
    TwitchChallengeBody,
    TwitchEventType,
)


logger = Logger(service="bryti")


class TwitchService:
    def handle_event(self, event_type: TwitchEventType, body: str) -> Response:
        logger.info("Received Twitch event", body=body)
        match event_type:
            case TwitchEventType.CHALLENGE:
                return self.handle_challenge(body)
            case TwitchEventType.NOTIFICATION:
                return self.handle_notification(body)
            case TwitchEventType.REVOCATION:
                return self.handle_revocation(body)

    def handle_challenge(self, body: str) -> Response:
        challenge_body = TwitchChallengeBody.model_validate_json(body)
        challenge = challenge_body.challenge
        logger.info("Responding to challenge event", challenge=challenge)
        return Response(
            status_code=HTTPStatus.OK,
            content_type=content_types.TEXT_PLAIN,
            body=challenge,
        )

    def handle_notification(self, body: str) -> Response:
        logger.info("Acknowledging notification event")
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({}),
        )

    def handle_revocation(self, body: str) -> Response:
        logger.info("Acknowledging revocation event")
        return Response(
            status_code=HTTPStatus.NO_CONTENT,
            content_type=content_types.APPLICATION_JSON,
            body=json.dumps({}),
        )
