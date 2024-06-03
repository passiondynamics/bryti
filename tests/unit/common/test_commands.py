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

from datetime import (
    datetime,
    timezone,
)


@pytest.fixture
def mock_api_interfaces():
    return APIInterfaces(MagicMock(), MagicMock())


@patch("src.common.commands.datetime")
def test_status_command(mock_datetime, mock_api_interfaces):
    mock_datetime.now.return_value = datetime(2006, 1, 2, 15, 4, 5, tzinfo=timezone.utc)
    expected = "Ok at 2006-01-02 @ 3:04:05pm UTC!"
    actual = StatusCommand(mock_api_interfaces, Permission.EVERYBODY).execute()
    assert actual == expected


def test_deaths_info_command(mock_api_interfaces):
    expected = "Not implemented yet!"
    actual = DeathsInfoCommand(mock_api_interfaces, Permission.EVERYBODY).execute()
    assert actual == expected


def test_deaths_add_command(mock_api_interfaces):
    expected = "Not implemented yet!"
    actual = DeathsAddCommand(mock_api_interfaces, Permission.EVERYBODY).execute()
    assert actual == expected


def test_deaths_set_command(mock_api_interfaces):
    expected = "Not implemented yet!"
    actual = DeathsSetCommand(mock_api_interfaces, Permission.EVERYBODY).execute(0)
    assert actual == expected


def test_twitch_connect_command(mock_api_interfaces):
    expected = "Not implemented yet!"
    actual = TwitchConnectCommand(mock_api_interfaces, Permission.EVERYBODY).execute()
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

