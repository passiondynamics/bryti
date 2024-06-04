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


MOCK_API_INTERFACES = APIInterfaces(MagicMock(), MagicMock())
@pytest.fixture
def mock_state():
    return State(user="mock-user")


@patch("src.common.commands.datetime")
def test_status_command(mock_datetime, mock_state):
    mock_datetime.now.return_value = datetime(2006, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    expected = "Ok at 2006-01-02 @ 3:04:05pm UTC!"
    actual = StatusCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
    assert actual == expected


def test_deaths_info_command_no_deaths(mock_state):
    actual = DeathsInfoCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"

    mock_state.deaths = DeathState(count=0, last_timestamp="2006-01-02T15:04:05Z")
    actual = DeathsInfoCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
    assert actual == "No deaths yet!"


def test_deaths_info_command_with_deaths(mock_state):
    mock_state.deaths = DeathState(count=4, last_timestamp="2006-01-02T15:04:05Z")
    actual = DeathsInfoCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
    assert actual == "Death count: 4\nLast death: 2006-01-02 @ 3:04:05pm UTC"


def test_deaths_add_command(mock_state):
    expected = "Not implemented yet!"
    actual = DeathsAddCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
    assert actual == expected


def test_deaths_set_command(mock_state):
    expected = "Not implemented yet!"
    actual = DeathsSetCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute(0)
    assert actual == expected


def test_twitch_connect_command(mock_state):
    expected = "Not implemented yet!"
    actual = TwitchConnectCommand(MOCK_API_INTERFACES, mock_state, Permission.EVERYBODY).execute()
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

