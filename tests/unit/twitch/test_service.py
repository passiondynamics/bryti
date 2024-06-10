from aws_lambda_powertools.event_handler import Response
import pytest

import json
from types import SimpleNamespace
from unittest.mock import (
    MagicMock,
    call,
    patch,
)

from src.common.state_models import (
    LookupFields,
    Permission,
    State,
)
from src.twitch.models import (
    TwitchEventType,
    TwitchHeaders,
)
from src.twitch.notification_models import TwitchChannelChatMessage
from src.twitch.service import (
    TwitchService,
    TwitchSignatureMismatchError,
)


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

DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE = {
    "broadcaster_user_id": "mock-broadcaster-id",
    "broadcaster_user_name": "mock-broadcaster-name",
    "broadcaster_user_login": "mock-broadcaster-login",
    "chatter_user_id": "mock-chatter-id",
    "chatter_user_name": "mock-chatter-name",
    "chatter_user_login": "mock-chatter-login",
    "message_id": "mock-message-id",
    "message": {
        "text": "mock-text",
        "fragments": [],
    },
    "message_type": "mock-message-type",
    "badges": [],
    "color": "mock-color",
}

MOCK_STREAM_ONLINE_EVENT = {
    "broadcaster_user_id": "mock-broadcaster-id",
    "broadcaster_user_login": "mock-broadcaster-login",
    "broadcaster_user_name": "mock-broadcaster-name",
    "id": "mock-id",
    "type": "mock-type",
    "started_at": "mock-timestamp",
}

MOCK_STREAM_OFFLINE_EVENT = {
    "broadcaster_user_id": "mock-broadcaster-id",
    "broadcaster_user_login": "mock-broadcaster-login",
    "broadcaster_user_name": "mock-broadcaster-name",
}


@pytest.fixture
def mock_api_interfaces():
    return MagicMock()


@pytest.fixture
def twitch_service(mock_api_interfaces):
    return TwitchService(mock_api_interfaces, "mock-user-id", "mock-command-prefix", None)


@pytest.mark.parametrize(
    "event_type, service_function_name",
    [
        (TwitchEventType.CHALLENGE, "handle_challenge"),
        (TwitchEventType.NOTIFICATION, "handle_notification"),
        (TwitchEventType.REVOCATION, "handle_revocation"),
    ],
)
@patch("src.twitch.service.TwitchService.verify_signature")
def test_handle_event(mock_verify_signature, twitch_service, event_type, service_function_name):
    headers = TwitchHeaders.model_validate({
        **DEFAULT_MOCK_HEADERS,
        "twitch-eventsub-message-type": event_type,
    })
    with patch(f"src.twitch.service.TwitchService.{service_function_name}") as mock_service_fn:
        twitch_service.handle_event(headers, "mock-body")

        mock_verify_signature.assert_called_with(headers, "mock-body")
        mock_service_fn.assert_called_with("mock-body")


def test_verify_signature(twitch_service):
    headers = TwitchHeaders.model_validate({
        **DEFAULT_MOCK_HEADERS,
        "twitch-eventsub-message-signature": "sha256=c0fe54c3d369473bcc76f00aabd90ce62b7497bece3add998cf99965d3228d2f",
    })
    body = "mock-body"
    twitch_service.verify_signature(headers, body)


def test_verify_signature_mismatch(twitch_service):
    headers = TwitchHeaders.model_validate({
        **DEFAULT_MOCK_HEADERS,
        "twitch-eventsub-message-signature": "c0fe54c3d369473bcc76f00aabd90ce62b7497bece3add998cf99965d3228d2f",
    })
    body = "mock-body-2"
    with pytest.raises(TwitchSignatureMismatchError) as e:
        twitch_service.verify_signature(headers, body)


def test_handle_challenge(twitch_service):
    body = {
        "challenge": "mock-challenge",
        "subscription": DEFAULT_MOCK_SUBSCRIPTION,
    }
    response = twitch_service.handle_challenge(json.dumps(body))

    assert response.status_code == 200
    assert response.content_type == "text/plain"
    assert response.body == "mock-challenge"


@pytest.mark.parametrize(
    "event, service_function_name",
    [
        (DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE, "handle_chat_message"),
        (MOCK_STREAM_ONLINE_EVENT, "handle_stream_event"),
        (MOCK_STREAM_OFFLINE_EVENT, "handle_stream_event"),
    ],
)
def test_handle_notification(twitch_service, event, service_function_name):
    body = {
        "event": event,
        "subscription": DEFAULT_MOCK_SUBSCRIPTION,
    }
    with patch(f"src.twitch.service.TwitchService.{service_function_name}") as mock_service_fn:
        response = twitch_service.handle_notification(json.dumps(body))

        assert response.status_code == 204
        assert response.content_type == "application/json"
        assert response.body == "{}"
        mock_service_fn.assert_called_once()


@patch("src.twitch.service.TwitchService.handle_chat_message")
def test_handle_notification_channel_chat_message_same_user_id(mock_handle_chat_message, twitch_service):
    body = {
        "event": {
            **DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE,
            "chatter_user_id": "mock-user-id",
        },
        "subscription": DEFAULT_MOCK_SUBSCRIPTION,
    }
    response = twitch_service.handle_notification(json.dumps(body))

    assert response.status_code == 204
    assert response.content_type == "application/json"
    assert response.body == "{}"
    mock_handle_chat_message.assert_not_called()


@pytest.mark.parametrize(
    "text",
    [
        (""),
        ("mock-text"),
        ("!non-command-prefix test"),
    ],
)
@patch("src.twitch.service.resolve_command")
def test_handle_chat_message_not_command_prefix(mock_resolve_command, twitch_service, text):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.message.text = text

    twitch_service.handle_chat_message(event)

    mock_resolve_command.assert_not_called()


@patch("src.twitch.service.resolve_command")
def test_handle_chat_message_nonexistant_command(mock_resolve_command, mock_api_interfaces, twitch_service):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.message.text = "!mock-command-prefix arg1 arg2 arg3"
    mock_resolve_command.return_value = (None, [])

    twitch_service.handle_chat_message(event)

    mock_resolve_command.assert_called_once_with(["arg1", "arg2", "arg3"])
    mock_api_interfaces.twitch.send_chat_message.assert_called_with(
        "mock-broadcaster-id",
        "mock-user-id",
        "Couldn't find that command!",
        reply_message_id="mock-message-id",
    )


@patch("src.twitch.service.TwitchService.retrieve_event_context")
@patch("src.twitch.service.resolve_command")
def test_handle_chat_message_cannot_invoke(mock_resolve_command, mock_retrieve_event_context, mock_api_interfaces, twitch_service):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.message.text = "!mock-command-prefix arg1 arg2 arg3"
    mock_command = MagicMock()
    mock_resolve_command.return_value = (mock_command, ["arg2", "arg3"])
    mock_state = MagicMock()
    mock_retrieve_event_context.return_value = (False, mock_state, Permission.EVERYBODY)

    twitch_service.handle_chat_message(event)

    mock_resolve_command.assert_called_once_with(["arg1", "arg2", "arg3"])
    mock_retrieve_event_context.assert_called_once_with(event)
    mock_command.assert_not_called()
    mock_api_interfaces.twitch.send_chat_message.assert_not_called()


@patch("src.twitch.service.TwitchService.retrieve_event_context")
@patch("src.twitch.service.resolve_command")
def test_handle_chat_message_bad_command(mock_resolve_command, mock_retrieve_event_context, mock_api_interfaces, twitch_service):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.message.text = "!mock-command-prefix arg1 arg2 arg3"
    mock_command = MagicMock()
    mock_command_obj = mock_command.return_value
    mock_command_obj.execute.side_effect = TypeError
    mock_resolve_command.return_value = (mock_command, ["arg2", "arg3"])
    mock_state = MagicMock()
    mock_retrieve_event_context.return_value = (True, mock_state, Permission.EVERYBODY)

    twitch_service.handle_chat_message(event)

    mock_resolve_command.assert_called_once_with(["arg1", "arg2", "arg3"])
    mock_retrieve_event_context.assert_called_once_with(event)
    mock_command.assert_called_once_with(mock_api_interfaces, mock_state, Permission.EVERYBODY)
    mock_command_obj.execute.assert_called_once_with("arg2", "arg3")
    mock_api_interfaces.twitch.send_chat_message.assert_called_with(
        "mock-broadcaster-id",
        "mock-user-id",
        "Invalid call to command!",
        reply_message_id="mock-message-id",
    )


@patch("src.twitch.service.TwitchService.retrieve_event_context")
@patch("src.twitch.service.resolve_command")
def test_handle_chat_message_valid_command(mock_resolve_command, mock_retrieve_event_context, mock_api_interfaces, twitch_service):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.message.text = "!mock-command-prefix arg1 arg2 arg3"
    mock_command = MagicMock()
    mock_command_obj = mock_command.return_value
    mock_command_obj.execute.return_value = "mock-reply"
    mock_resolve_command.return_value = (mock_command, ["arg2", "arg3"])
    mock_state = MagicMock()
    mock_retrieve_event_context.return_value = (True, mock_state, Permission.EVERYBODY)

    twitch_service.handle_chat_message(event)

    mock_resolve_command.assert_called_once_with(["arg1", "arg2", "arg3"])
    mock_command.assert_called_once_with(mock_api_interfaces, mock_state, Permission.EVERYBODY)
    mock_command_obj.execute.assert_called_once_with("arg2", "arg3")
    mock_api_interfaces.twitch.send_chat_message.assert_called_with(
        "mock-broadcaster-id",
        "mock-user-id",
        "mock-reply",
        reply_message_id="mock-message-id",
    )


@pytest.mark.parametrize(
    "chatter_user_id, permission",
    [
        ("mock-broadcaster-id", Permission.BROADCASTER),
        ("mock-chatter-id", Permission.EVERYBODY),
    ],
)
def test_retrieve_event_context_no_lookup(mock_api_interfaces, twitch_service, chatter_user_id, permission):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.chatter_user_id = chatter_user_id

    mock_api_interfaces.state_table.lookup_by_twitch.return_value = None
    state = State(user="mock-broadcaster-login", twitch_user_id="mock-broadcaster-id")
    expected = (True, state, permission)

    actual = twitch_service.retrieve_event_context(event)

    assert actual == expected
    assert mock_api_interfaces.state_table.lookup_by_twitch.call_args_list == [
        call("mock-broadcaster-id"),
        call(chatter_user_id),
    ]
    mock_api_interfaces.state_table.get_state.assert_not_called()


@pytest.mark.parametrize(
    "chatter_user_id, permission",
    [
        ("mock-broadcaster-id", Permission.BROADCASTER),
        ("mock-chatter-id", Permission.EVERYBODY),
    ],
)
def test_retrieve_event_context_broadcaster_lookup(mock_api_interfaces, twitch_service, chatter_user_id, permission):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.chatter_user_id = chatter_user_id

    def mock_lookup_by_twitch(twitch_user_id: str):
        if twitch_user_id == "mock-broadcaster-id":
            return LookupFields(user="mock-broadcaster-login")

        return None

    mock_api_interfaces.state_table.lookup_by_twitch.side_effect = mock_lookup_by_twitch
    state = State(user="mock-broadcaster-login", twitch_user_id="mock-broadcaster-id")
    mock_api_interfaces.state_table.get_state.return_value = state
    expected = (True, state, permission)

    actual = twitch_service.retrieve_event_context(event)

    assert actual == expected
    assert mock_api_interfaces.state_table.lookup_by_twitch.call_args_list == [
        call("mock-broadcaster-id"),
        call(chatter_user_id),
    ]
    mock_api_interfaces.state_table.get_state.assert_called_once_with("mock-broadcaster-login")


@pytest.mark.parametrize(
    "chatter_user_id, permission",
    [
        ("mock-broadcaster-id", Permission.BROADCASTER),
        ("mock-chatter-id", Permission.EVERYBODY),
    ],
)
def test_retrieve_event_context_chatter_lookup(mock_api_interfaces, twitch_service, chatter_user_id, permission):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.chatter_user_id = chatter_user_id

    def mock_lookup_by_twitch(twitch_user_id: str):
        if twitch_user_id == "mock-chatter-id":
            return LookupFields(user="mock-chatter-login")

        return None

    mock_api_interfaces.state_table.lookup_by_twitch.side_effect = mock_lookup_by_twitch
    state = State(user="mock-broadcaster-login", twitch_user_id="mock-broadcaster-id")
    expected = (True, state, permission)

    actual = twitch_service.retrieve_event_context(event)

    assert actual == expected
    assert mock_api_interfaces.state_table.lookup_by_twitch.call_args_list == [
        call("mock-broadcaster-id"),
        call(chatter_user_id),
    ]
    mock_api_interfaces.state_table.get_state.assert_not_called()


@pytest.mark.parametrize(
    "chatter_user_id, permission",
    [
        ("mock-broadcaster-id", Permission.BROADCASTER),
        ("mock-chatter-id", Permission.EVERYBODY),
        ("mock-chatter-id-2", Permission.MODERATOR),
    ],
)
def test_retrieve_event_context_both_lookups(mock_api_interfaces, twitch_service, chatter_user_id, permission):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.chatter_user_id = chatter_user_id

    def mock_lookup_by_twitch(twitch_user_id: str):
        if twitch_user_id == "mock-broadcaster-id":
            return LookupFields(user="mock-broadcaster-login")
        elif twitch_user_id == "mock-chatter-id":
            return LookupFields(user="mock-chatter-login")
        elif twitch_user_id == "mock-chatter-id-2":
            return LookupFields(user="mock-chatter-login-2")

    mock_api_interfaces.state_table.lookup_by_twitch.side_effect = mock_lookup_by_twitch
    state = State(user="mock-broadcaster-login", twitch_user_id="mock-broadcaster-id", members={"mock-chatter-login-2": Permission.MODERATOR})
    mock_api_interfaces.state_table.get_state.return_value = state
    expected = (True, state, permission)

    actual = twitch_service.retrieve_event_context(event)

    assert actual == expected
    assert mock_api_interfaces.state_table.lookup_by_twitch.call_args_list == [
        call("mock-broadcaster-id"),
        call(chatter_user_id),
    ]
    mock_api_interfaces.state_table.get_state.assert_called_once_with("mock-broadcaster-login")


@pytest.mark.parametrize(
    "github_user_id, can_invoke",
    [
        ("mock-github-user-id", True),
        ("mock-github-user-id-2", False),
    ],
)
def test_retrieve_event_context_can_invoke(mock_api_interfaces, twitch_service, github_user_id, can_invoke):
    event = TwitchChannelChatMessage(**DEFAULT_MOCK_CHANNEL_CHAT_MESSAGE)
    event.chatter_user_id = "mock-chatter-id"
    twitch_service.assignee_ids = ["mock-github-user-id"]

    def mock_lookup_by_twitch(twitch_user_id: str):
        if twitch_user_id == "mock-chatter-id":
            return LookupFields(user="mock-chatter-login", github_user_id=github_user_id)

        return None

    mock_api_interfaces.state_table.lookup_by_twitch.side_effect = mock_lookup_by_twitch
    state = State(user="mock-broadcaster-login", twitch_user_id="mock-broadcaster-id")
    expected = (can_invoke, state, Permission.EVERYBODY)

    actual = twitch_service.retrieve_event_context(event)

    assert actual == expected
    assert mock_api_interfaces.state_table.lookup_by_twitch.call_args_list == [
        call("mock-broadcaster-id"),
        call("mock-chatter-id"),
    ]
    mock_api_interfaces.state_table.get_state.assert_not_called()


def test_handle_revocation(twitch_service):
    body = {"subscription": DEFAULT_MOCK_SUBSCRIPTION}
    response = twitch_service.handle_revocation(json.dumps(body))

    assert response.status_code == 204
    assert response.content_type == "application/json"
    assert response.body == "{}"
