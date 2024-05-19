from aws_lambda_powertools.event_handler import Response
import pytest

import json
from types import SimpleNamespace
from unittest.mock import patch

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
            TwitchService().handle_event(headers, "mock-body")
            mock_verify_signature.assert_called_with(headers, "mock-body")
            mock_service_fn.assert_called_with("mock-body")

    def test_verify_signature(self):
        headers = TwitchHeaders.model_validate({
            **DEFAULT_MOCK_HEADERS,
            "twitch-eventsub-message-signature": "sha256=c0fe54c3d369473bcc76f00aabd90ce62b7497bece3add998cf99965d3228d2f",
        })
        body = "mock-body"
        TwitchService().verify_signature(headers, body)

    def test_handle_challenge(self):
        body = {
            "challenge": "mock-challenge",
            "subscription": DEFAULT_MOCK_SUBSCRIPTION,
        }
        response = TwitchService().handle_challenge(json.dumps(body))

        assert response.status_code == 200
        assert response.content_type == "text/plain"
        assert response.body == "mock-challenge"

    def test_handle_notification(self):
        body = {
            "event": {
                "broadcaster_user_id": "mock-id",
                "broadcaster_user_login": "mock-login",
                "broadcaster_user_name": "mock-name",
            },
            "subscription": DEFAULT_MOCK_SUBSCRIPTION,
        }
        response = TwitchService().handle_notification(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"

    def test_handle_revocation(self):
        body = {"subscription": DEFAULT_MOCK_SUBSCRIPTION}
        response = TwitchService().handle_revocation(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"
