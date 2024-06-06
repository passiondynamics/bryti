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


def test_deaths_info_command_no_deaths(mock_api_interfaces, mock_state):
    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"

    mock_state.deaths = DeathState(count=0, last_timestamp="2006-01-02T15:04:05Z")
    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"


def test_deaths_info_command_with_deaths(mock_api_interfaces, mock_state):
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")
    actual = DeathsInfoCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()
    assert actual == "Death count: 4 | Last death: 2006-01-02 @ 3:04:05pm UTC"


@patch("src.common.commands.datetime")
def test_deaths_add_command(mock_datetime, mock_api_interfaces, mock_state):
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")
    mock_datetime.now.return_value = datetime(2024, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    updated_state = State(
        user="mock-user",
        deaths=DeathState(
            count=5,
            last_timestamp="2024-01-02T15:04:05Z",
        ),
    )
    mock_api_interfaces.state_table.update_state.return_value = updated_state

    actual = DeathsAddCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute()

    assert actual == "Death count: 5 | Last death: 2024-01-02 @ 3:04:05pm UTC"
    mock_api_interfaces.state_table.update_state.assert_called_once_with(updated_state)


def test_deaths_set_command(mock_api_interfaces, mock_state):
    expected = "Not implemented yet!"
    actual = DeathsSetCommand(mock_api_interfaces, mock_state, Permission.EVERYBODY).execute(0)
    assert actual == expected


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

