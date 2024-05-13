from aws_lambda_powertools.event_handler import Response
import pytest

from types import SimpleNamespace
from unittest.mock import patch

from src.twitch.models import TwitchEventType
from src.twitch.service import TwitchService


class TestTwitchService:
    @pytest.mark.parametrize(
        "event_type, service_function_name",
        [
            (TwitchEventType.CHALLENGE, "handle_challenge"),
            (TwitchEventType.NOTIFICATION, "handle_notification"),
            (TwitchEventType.REVOCATION, "handle_revocation"),
        ],
    )
    @patch("src.twitch.service.TwitchService.handle_challenge")
    def test_handle_event(self, mock_handle_challenge, event_type, service_function_name):
        with patch(f"src.twitch.service.TwitchService.{service_function_name}") as mock_service_fn:
            TwitchService().handle_event(event_type, "mock-body")
            mock_service_fn.assert_called_with("mock-body")

    def test_handle_challenge(self):
        body = '{"challenge": "mock-challenge"}'
        response = TwitchService().handle_challenge(body)

        assert response.status_code == 200
        assert response.content_type == "text/plain"
        assert response.body == "mock-challenge"

    def test_handle_notification(self):
        response = TwitchService().handle_notification("")

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"

    def test_handle_revocation(self):
        response = TwitchService().handle_revocation("")

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"
