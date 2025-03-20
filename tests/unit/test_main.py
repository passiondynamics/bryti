from aws_lambda_powertools.event_handler import Response
import pytest

from types import SimpleNamespace
from unittest.mock import patch

from src.discord.service import DiscordSignatureMismatchError
from src.twitch.service import TwitchSignatureMismatchError


MOCK_CONTEXT = SimpleNamespace(**{
    "function_name": "mock-function-name",
    "memory_limit_in_mb": "mock-limit",
    "invoked_function_arn": "mock-arn",
    "aws_request_id": "mock-request-id",
})

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

MOCK_DISCORD_EVENT = {
    "requestContext": {
        "http": {"method": "POST"},
        "stage": "$default",
    },
    "rawPath": "/bryti",
    "headers": {
        "x-signature-ed25519": "mock-signature",
        "x-signature-timestamp": "mock-timestamp",
    },
    "body": "mock-body",
}


@patch("src.discord.service.DiscordService.handle_event")
@patch("src.twitch.service.TwitchService.handle_event")
@patch("boto3.client")
def test_bryti_handler_twitch(_mock_boto3_client, mock_twitch_handle_event, mock_discord_handle_event):
    # Local import here to patch global variables/imports in `main.py` first.
    from src import main

    mock_twitch_handle_event.return_value = Response(
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
    assert mock_twitch_handle_event.call_count == 1
    assert mock_discord_handle_event.call_count == 0


@patch("src.discord.service.DiscordService.handle_event")
@patch("src.twitch.service.TwitchService.handle_event")
@patch("boto3.client")
def test_bryti_handler_twitch_signature_mismatch(_mock_boto3_client, mock_twitch_handle_event, mock_discord_handle_event):
    from src import main

    mock_twitch_handle_event.side_effect = TwitchSignatureMismatchError()
    expected = {
        "isBase64Encoded": False,
        "statusCode": 403,
        "body": "{}",
        "headers": {"Content-Type": "application/json"},
        "cookies": [],
    }

    actual = main.app.resolve(MOCK_TWITCH_EVENT, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_handle_event.call_count == 1
    assert mock_discord_handle_event.call_count == 0


@patch("src.discord.service.DiscordService.handle_event")
@patch("src.twitch.service.TwitchService.handle_event")
@patch("boto3.client")
def test_bryti_handler_discord(_mock_boto3_client, mock_twitch_handle_event, mock_discord_handle_event):
    from src import main

    mock_discord_handle_event.return_value = Response(
        status_code=200,
        content_type="application/json",
        body='{"type": 1}',
    )
    expected = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": '{"type": 1}',
        "headers": {"Content-Type": "application/json"},
        "cookies": [],
    }

    actual = main.app.resolve(MOCK_DISCORD_EVENT, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_handle_event.call_count == 0
    assert mock_discord_handle_event.call_count == 1


@patch("src.discord.service.DiscordService.handle_event")
@patch("src.twitch.service.TwitchService.handle_event")
@patch("boto3.client")
def test_bryti_handler_twitch_signature_mismatch(_mock_boto3_client, mock_twitch_handle_event, mock_discord_handle_event):
    from src import main

    mock_discord_handle_event.side_effect = DiscordSignatureMismatchError()
    expected = {
        "isBase64Encoded": False,
        "statusCode": 403,
        "body": "{}",
        "headers": {"Content-Type": "application/json"},
        "cookies": [],
    }

    actual = main.app.resolve(MOCK_DISCORD_EVENT, MOCK_CONTEXT)

    assert actual == expected
    assert mock_twitch_handle_event.call_count == 0
    assert mock_discord_handle_event.call_count == 1


@patch("src.twitch.service.TwitchService.handle_event")
@patch("src.twitch.interface.TwitchInterface")
@patch("boto3.client")
def test_bryti_handler_unknown_event_source(_mock_boto3_client, _mock_twitch_interface, mock_handle_event):
    from src import main

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
    assert mock_handle_event.call_count == 0
