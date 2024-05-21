from aws_lambda_powertools.event_handler import Response
import pytest

import json
from types import SimpleNamespace
from unittest.mock import (
    MagicMock,
    patch,
)

from src.twitch.models import (
    TwitchEventType,
    TwitchHeaders,
)
from src.twitch.service import TwitchService


DEFAULT_MOCK_HEADERS = {
    "twitch-eventsub-message-id": "mock-id",
    "twitch-eventsub-message-type": "notification",
    "twitch-eventsub-subscription-type": "mock-subscription-type",
    "twitch-eventsub-subscription-version": "0",
    "twitch-eventsub-message-timestamp": "mock-timestamp",
    "twitch-eventsub-message-signature": "mock-signature",
    "twitch-eventsub-message-retry": "0",
}

DEFAULT_MOCK_SUBSCRIPTION = {
    "id": "mock-id",
    "type": "mock-subscription-type",
    "version": 0,
    "status": "mock-status",
    "cost": 0,
    "condition": {},
    "created_at": "mock-timestamp",
    "transport": {
        "method": "webhook",
        "callback": "mock-callback",
    },
}

MOCK_STREAM_ONLINE_EVENT = {
    "broadcaster_user_id": "mock-broadcaster-id",
    "broadcaster_user_login": "mock-login",
    "broadcaster_user_name": "mock-name",
    "id": "mock-id",
    "type": "mock-type",
    "started_at": "mock-timestamp",
}

MOCK_STREAM_OFFLINE_EVENT = {
    "broadcaster_user_id": "mock-id",
    "broadcaster_user_login": "mock-login",
    "broadcaster_user_name": "mock-name",
}


class TestTwitchService:
    @pytest.mark.parametrize(
        "event_type, service_function_name",
        [
            (TwitchEventType.CHALLENGE, "handle_challenge"),
            (TwitchEventType.NOTIFICATION, "handle_notification"),
            (TwitchEventType.REVOCATION, "handle_revocation"),
        ],
    )
    @patch("src.twitch.service.TwitchService.verify_signature")
    def test_handle_event(self, mock_verify_signature, event_type, service_function_name):
        headers = TwitchHeaders.model_validate({
            **DEFAULT_MOCK_HEADERS,
            "twitch-eventsub-message-type": event_type,
        })
        with patch(f"src.twitch.service.TwitchService.{service_function_name}") as mock_service_fn:
            TwitchService("mock-command-prefix").handle_event(headers, "mock-body")
            mock_verify_signature.assert_called_with(headers, "mock-body")
            mock_service_fn.assert_called_with("mock-body")

    def test_verify_signature(self):
        headers = TwitchHeaders.model_validate({
            **DEFAULT_MOCK_HEADERS,
            "twitch-eventsub-message-signature": "sha256=c0fe54c3d369473bcc76f00aabd90ce62b7497bece3add998cf99965d3228d2f",
        })
        body = "mock-body"
        TwitchService("mock-command-prefix").verify_signature(headers, body)

    def test_handle_challenge(self):
        body = {
            "challenge": "mock-challenge",
            "subscription": DEFAULT_MOCK_SUBSCRIPTION,
        }
        response = TwitchService("mock-command-prefix").handle_challenge(json.dumps(body))

        assert response.status_code == 200
        assert response.content_type == "text/plain"
        assert response.body == "mock-challenge"

    @pytest.mark.parametrize(
        "event",
        [
            (MOCK_STREAM_ONLINE_EVENT),
            (MOCK_STREAM_OFFLINE_EVENT),
        ],
    )
    def test_handle_notification_non_channel_chat_message(self, event):
        body = {
            "event": event,
            "subscription": DEFAULT_MOCK_SUBSCRIPTION,
        }
        # TODO: mock Discord interface and assert called.
        response = TwitchService("mock-command-prefix").handle_notification(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"

    @pytest.mark.parametrize(
        "text, should_call_resolve_command, should_call_command",
        [
            ("", False, False),
            ("mock-text", False, False),
            ("!non-command-prefix test", False, False),
            ("!mock-command-prefix non-command", True, False),
            ("!mock-command-prefix command", True, True),
        ],
    )
    @patch("src.twitch.service.resolve_command")
    def test_handle_notification_channel_chat_message(self, mock_resolve_command, text, should_call_resolve_command, should_call_command):
        body = {
            "event": {
                "broadcaster_user_id": "mock-broadcaster-id",
                "broadcaster_user_name": "mock-broadcaster-name",
                "broadcaster_user_login": "mock-broadcaster-login",
                "chatter_user_id": "mock-chatter-id",
                "chatter_user_name": "mock-chatter-name",
                "chatter_user_login": "mock-chatter-login",
                "message_id": "mock-message-id",
                "message": {
                    "text": text,
                    "fragments": [],
                },
                "message_type": "mock-message-type",
                "badges": [],
                "color": "mock-color",
            },
            "subscription": DEFAULT_MOCK_SUBSCRIPTION,
        }
        if should_call_command:
            mock_command = MagicMock()
            mock_command_obj = mock_command.return_value
            mock_command_obj.execute.return_value = "mock-response"
            mock_resolve_command.return_value = (mock_command, [])
        else:
            mock_resolve_command.return_value = (None, [])

        response = TwitchService("mock-command-prefix").handle_notification(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"
        assert mock_resolve_command.called == should_call_resolve_command
        if should_call_command:
            assert mock_command_obj.execute.called == should_call_command

    def test_handle_revocation(self):
        body = {"subscription": DEFAULT_MOCK_SUBSCRIPTION}
        response = TwitchService("mock-command-prefix").handle_revocation(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"
