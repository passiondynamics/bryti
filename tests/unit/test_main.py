from aws_lambda_powertools.event_handler import Response
import pytest

from types import SimpleNamespace
from unittest.mock import patch

from src import main


MOCK_CONTEXT = SimpleNamespace(**{
    "function_name": "mock-function-name",
    "memory_limit_in_mb": "mock-limit",
    "invoked_function_arn": "mock-arn",
    "aws_request_id": "mock-request-id",
})


class TestMain:
    @patch("src.main.twitch_service")
    def test_bryti_handler_twitch(self, mock_twitch_service):
        mock_twitch_service.handle_event.return_value = Response(
            status_code=200,
            content_type="text/plain",
            body="mock-challenge",
        )
        event = {
            "requestContext": {
                "http": {"method": "POST"},
                "stage": "$default",
            },
            "rawPath": "/bryti",
            "headers": {
                "twitch-eventsub-message-type": "webhook_callback_verification",
            },
            "body": '{"challenge": "mock-challenge"}',
        }
        expected = {
            "isBase64Encoded": False,
            "statusCode": 200,
            "body": "mock-challenge",
            "headers": {"Content-Type": "text/plain"},
            "cookies": [],
        }

        actual = main.app.resolve(event, MOCK_CONTEXT)

        assert actual == expected
        assert mock_twitch_service.handle_event.call_count == 1

    @patch("src.main.twitch_service")
    def test_bryti_handler_default(self, mock_twitch_service):
        event = {
            "requestContext": {
                "http": {"method": "POST"},
                "stage": "$default",
            },
            "rawPath": "/bryti",
        }
        expected = {
            "isBase64Encoded": False,
            "statusCode": 204,
            "body": "{}",
            "headers": {"Content-Type": "application/json"},
            "cookies": [],
        }

        actual = main.app.resolve(event, MOCK_CONTEXT)

        assert actual == expected
        assert mock_twitch_service.handle_event.call_count == 0

