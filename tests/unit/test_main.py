from aws_lambda_powertools.event_handler import Response
import pytest

from types import SimpleNamespace
from unittest.mock import patch

from src import main
from src.twitch.service import TwitchSignatureMismatchError


MOCK_CONTEXT = SimpleNamespace(**{
    "function_name": "mock-function-name",
    "memory_limit_in_mb": "mock-limit",
    "invoked_function_arn": "mock-arn",
    "aws_request_id": "mock-request-id",
})

MOCK_ENV_VARS = {
    "TWITCH_CLIENT_ID": "mock-client-id",
    "TWITCH_CLIENT_SECRET": "mock-client-secret",
    "TWITCH_USER_ID": "mock-user-id",
    "COMMAND_PREFIX": "mock-command-prefix",
}

MOCK_TWITCH_EVENT = {
    "requestContext": {
        "http": {"method": "POST"},
        "stage": "$default",
    },
    "rawPath": "/bryti",
    "headers": {
        "twitch-eventsub-message-id": "mock-id",
        "twitch-eventsub-message-type": "notification",
        "twitch-eventsub-subscription-type": "mock-event-type",
        "twitch-eventsub-subscription-version": "0",
        "twitch-eventsub-message-timestamp": "mock-timestamp",
        "twitch-eventsub-message-signature": "mock-signature",
        "twitch-eventsub-message-retry": "0",
    },
    "body": "mock-body",
}


@patch("src.main.twitch_service")
def test_bryti_handler_twitch(mock_twitch_service):
    mock_twitch_service.handle_event.return_value = Response(
        status_code=200,
        content_type="text/plain",
        body="mock-challenge",
    )
    expected = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": "mock-challenge",
        "headers": {"Content-Type": "text/plain"},
        "cookies": [],
    }

    actual = main.app.resolve(MOCK_TWITCH_EVENT, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_service.handle_event.call_count == 1


@patch("src.main.twitch_service")
def test_bryti_handler_twitch_signature_mismatch( mock_twitch_service):
    mock_twitch_service.handle_event.side_effect = TwitchSignatureMismatchError()
    expected = {
        "isBase64Encoded": False,
        "statusCode": 403,
        "body": "{}",
        "headers": {"Content-Type": "application/json"},
        "cookies": [],
    }

    actual = main.app.resolve(MOCK_TWITCH_EVENT, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_service.handle_event.call_count == 1


@patch("src.main.twitch_service")
def test_bryti_handler_unknown_event_source(mock_twitch_service):
    event = {
        "requestContext": {
            "http": {"method": "POST"},
            "stage": "$default",
        },
        "rawPath": "/bryti",
    }
    expected = {
        "isBase64Encoded": False,
        "statusCode": 401,
        "body": "{}",
        "headers": {"Content-Type": "application/json"},
        "cookies": [],
    }

    actual = main.app.resolve(event, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_service.handle_event.call_count == 0
