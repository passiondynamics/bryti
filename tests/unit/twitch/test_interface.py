import requests_mock
import pytest

from typing import List
from unittest.mock import patch

from src.twitch.interface import (
    TwitchError,
    TwitchInterface,
)
from src.twitch.models import (
    TwitchEventSubscription,
    TwitchEventSubscriptionCondition,
    TwitchEventSubscriptionTransport,
)


@pytest.fixture
def twitch_interface():
    with patch("src.twitch.interface.TwitchInterface.validate_token"):
        yield TwitchInterface("mock-client-id", "mock-client-secret", bearer_token="mock-bearer-token")


@patch("src.twitch.interface.TwitchInterface.validate_token")
@patch("src.twitch.interface.TwitchInterface.get_client_credentials_token")
def test_init(mock_get_client_credentials, mock_validate_token):
    mock_get_client_credentials.return_value = "mock-bearer-token"

    TwitchInterface("mock-client-id", "mock-client-secret")

    mock_get_client_credentials.assert_called_once()
    mock_validate_token.assert_called_once()


def test_send_request(twitch_interface):
    url = "https://api.twitch.tv/mock/endpoint"
    headers = {"mock-header-key": "mock-header-value"}
    response = {"mock-response-key": "mock-response-value"}
    with requests_mock.Mocker() as mock_requests:
        mock_requests.get(url, request_headers=headers, json=response)
        actual = twitch_interface._send_request("GET", url, headers)
        assert actual == response

        mock_requests.post(url, request_headers=headers, json=response)
        actual = twitch_interface._send_request("POST", url, headers)
        assert actual == response

        mock_requests.post(url, request_headers=headers, json={"data": response})
        actual = twitch_interface._send_request("POST", url, headers, DataType=dict)
        assert actual == response

        mock_requests.post(url, request_headers=headers, status_code=401)
        with pytest.raises(TwitchError) as e:
            twitch_interface._send_request("POST", url, headers, DataType=dict)
            assert e == True


@patch("src.twitch.interface.TwitchInterface._send_request")
def test_get_client_credentials_token(mock_send_request, twitch_interface):
    expected_payload = {
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
        "grant_type": "client_credentials",
    }
    mock_send_request.return_value = {"access_token": "mock-bearer-token"}

    actual = twitch_interface.get_client_credentials_token()

    mock_send_request.assert_called_once_with("POST", "https://id.twitch.tv/oauth2/token", payload=expected_payload)
    assert actual == "mock-bearer-token"


@patch("src.twitch.interface.TwitchInterface._send_request")
def test_validate_token(mock_send_request):
    expected_headers = {"Authorization": "Bearer mock-bearer-token"}
    TwitchInterface("mock-client-id", "mock-client-secret", bearer_token="mock-bearer-token")
    mock_send_request.assert_called_once_with("GET", "https://id.twitch.tv/oauth2/validate", headers=expected_headers)


@patch("src.twitch.interface.TwitchInterface._send_request")
def test_get_event_subscriptions(mock_send_request, twitch_interface):
    expected_headers = {
        "Authorization": "Bearer mock-bearer-token",
        "Client-Id": "mock-client-id",
    }

    actual = twitch_interface.get_event_subscriptions()

    mock_send_request.assert_called_once_with(
        "GET",
        "https://api.twitch.tv/helix/eventsub/subscriptions",
        headers=expected_headers,
        DataType=List[TwitchEventSubscription],
    )


@patch("src.twitch.interface.TwitchInterface._send_request")
def test_create_event_subscription(mock_send_request, twitch_interface):
    expected_headers = {
        "Authorization": "Bearer mock-bearer-token",
        "Client-Id": "mock-client-id",
    }
    expected_condition = {"mock-key": "mock-value"}
    transport = {"mock-key": "mock-value"}
    expected_payload = {
        "type": "mock-type",
        "version": "1",
        "condition": expected_condition,
        "transport": {**transport, "secret": "bryti.mock-type.1"}
    }

    actual = twitch_interface.create_event_subscription("mock-type", "1", expected_condition, transport)

    mock_send_request.assert_called_once_with(
        "POST",
        "https://api.twitch.tv/helix/eventsub/subscriptions",
        headers=expected_headers,
        payload=expected_payload,
        DataType=List[TwitchEventSubscription],
    )


@patch("src.twitch.interface.TwitchInterface._send_request")
def test_send_chat_message(mock_send_request, twitch_interface):
    expected_headers = {
        "Authorization": "Bearer mock-bearer-token",
        "Client-Id": "mock-client-id",
    }
    expected_payload = {
        "broadcaster_id": "mock-broadcaster-id",
        "sender_id": "mock-sender-id",
        "message": "mock-message",
        "reply_parent_message_id": "mock-message-id",
    }

    actual = twitch_interface.send_chat_message("mock-broadcaster-id", "mock-sender-id", "mock-message", "mock-message-id")

    mock_send_request.assert_called_once_with(
        "POST",
        "https://api.twitch.tv/helix/chat/messages",
        headers=expected_headers,
        payload=expected_payload,
    )
