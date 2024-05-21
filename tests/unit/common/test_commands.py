from unittest.mock import (
    MagicMock,
    patch,
)
import pytest

from src.common.commands import (
    StatusCommand,
    DeathsInfoCommand,
    DeathsAddCommand,
    DeathsSetCommand,
    TwitchConnectCommand,
    resolve_command,
)


class TestCommands:
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
    def test_resolve_command(self, args, expected):
        actual = resolve_command(args)
        assert actual == expected

