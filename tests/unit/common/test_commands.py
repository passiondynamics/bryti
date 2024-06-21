from unittest.mock import (
    MagicMock,
    patch,
)
import pytest

from src.common.api_interfaces import APIInterfaces
from src.common.commands import (
    Permission,
    StatusCommand,
    DeathsInfoCommand,
    DeathsAddCommand,
    DeathsSetCommand,
    TwitchConnectCommand,
    resolve_command,
)
from src.common.state_models import (
    DeathState,
    State,
)

from datetime import (
    datetime,
    timezone,
)


@pytest.fixture
def mock_api_interfaces():
    return APIInterfaces(MagicMock(), MagicMock())

@pytest.fixture
def mock_state():
    return State(user="mock-user")


@patch("src.common.commands.datetime")
def test_status_command(mock_datetime, mock_api_interfaces, mock_state):
    mock_datetime.now.return_value = datetime(2006, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    actual = StatusCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "Ok at 2006-01-02 @ 3:04:05pm UTC!"


def test_deaths_info_command_no_deaths_state(mock_api_interfaces, mock_state):
    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"

    mock_state.deaths = DeathState(count=0, last_timestamp="2006-01-02T15:04:05Z")
    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"


@pytest.mark.parametrize(
    "datetime_args, time_since_str",
    [
        ([2006, 1, 2, 15, 4, 5], "just now"),
        ([2006, 1, 2, 15, 4, 6], "1s ago"),
        ([2006, 1, 2, 15, 6, 5], "2m ago"),
        ([2006, 1, 2, 18, 4, 5], "3h ago"),
        ([2006, 1, 6, 15, 4, 5], "4d ago"),
        ([2006, 1, 6, 18, 6, 6], "4d3h2m1s ago"),
    ],
)
@patch("src.common.commands.datetime")
def test_deaths_info_command_with_deaths(mock_datetime, mock_api_interfaces, mock_state, datetime_args, time_since_str):
    mock_datetime.now.return_value = datetime(*datetime_args, tzinfo=timezone.utc)
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")

    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()

    assert actual == f"Death count: 4 | Last death: {time_since_str}"


def test_deaths_add_command_bad_permissions(mock_api_interfaces, mock_state):
    actual = DeathsAddCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "You don't have permissions for that!"


@pytest.mark.parametrize(
    "permission",
    [Permission.MODERATOR, Permission.BROADCASTER],
)
@patch("src.common.commands.datetime")
def test_deaths_add_command_within_window(mock_datetime, mock_api_interfaces, mock_state, permission):
    mock_datetime.now.return_value = datetime(2006, 1, 2, 15, 4, 14, tzinfo=timezone.utc)
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")

    actual = DeathsAddCommand(mock_api_interfaces, mock_state, permission).execute()

    assert actual == "It's been too soon since they last died! Are you sure they died again?"


@pytest.mark.parametrize(
    "permission",
    [Permission.MODERATOR, Permission.BROADCASTER],
)
@patch("src.common.commands.datetime")
def test_deaths_add_command(mock_datetime, mock_api_interfaces, mock_state, permission):
    mock_datetime.now.return_value = datetime(2024, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")
    updated_state = State(
        user="mock-user",
        deaths=DeathState(
            count=5,
            last_timestamp="2024-01-02T15:04:05Z",
        ),
    )
    mock_api_interfaces.state_table.update_state.return_value = updated_state

    actual = DeathsAddCommand(mock_api_interfaces, mock_state, permission).execute()

    assert actual == "Death count: 5 | Last death: just now"
    mock_api_interfaces.state_table.update_state.assert_called_once_with(updated_state)


@patch("src.common.commands.datetime")
def test_deaths_add_command_no_deaths_state(mock_datetime, mock_api_interfaces, mock_state):
    mock_datetime.now.return_value = datetime(2006, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    updated_state = State(
        user="mock-user",
        deaths=DeathState(
            count=1,
            last_timestamp="2006-01-02T15:04:05Z",
        ),
    )
    mock_api_interfaces.state_table.update_state.return_value = updated_state

    actual = DeathsAddCommand(mock_api_interfaces, mock_state, Permission.MODERATOR).execute()

    assert actual == "Death count: 1 | Last death: just now"
    mock_api_interfaces.state_table.update_state.assert_called_once_with(updated_state)


@pytest.mark.parametrize(
    "permission",
    [Permission.EVERYBODY, Permission.MODERATOR],
)
def test_deaths_set_command_bad_permissions(mock_api_interfaces, mock_state, permission):
    actual = DeathsSetCommand(mock_api_interfaces, mock_state, permission).execute(0)
    assert actual == "You don't have permissions for that!"


@patch("src.common.commands.datetime")
def test_deaths_set_command(mock_datetime, mock_api_interfaces, mock_state):
    mock_datetime.now.return_value = datetime(2024, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")
    updated_state = State(
        user="mock-user",
        deaths=DeathState(
            count=7,
            last_timestamp="2024-01-02T15:04:05Z",
        ),
    )
    mock_api_interfaces.state_table.update_state.return_value = updated_state

    actual = DeathsSetCommand(mock_api_interfaces, mock_state, Permission.BROADCASTER).execute(7)

    assert actual == "Death count: 7 | Last death: just now"
    mock_api_interfaces.state_table.update_state.assert_called_once_with(updated_state)


def test_twitch_connect_command(mock_api_interfaces, mock_state):
    expected = "Not implemented yet!"
    actual = TwitchConnectCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        # No args.
        ([], (None, [])),

        # Bad top-level args.
        ([None], (None, [])),
        ([""], (None, [])),
        (["nonexistant"], (None, [])),

        # Existing top-level command.
        (["status"], (StatusCommand, [])),

        # Existing command group w/ no-arg default.
        (["deaths"], (DeathsInfoCommand, [])),
        (["deaths", "add"], (DeathsAddCommand, [])),
        (["deaths", "set", "0"], (DeathsSetCommand, ["0"])),    # Validate remaining args.
        (["deaths", "nonexistant"], (None, [])),                # Bad nested-level args.

        # Existing command group w/o no-arg default.
        (["twitch"], (None, [])),
        (["twitch", "connect"], (TwitchConnectCommand, [])),
    ],
)
def test_resolve_command(args, expected):
    actual = resolve_command(args)
    assert actual == expected

