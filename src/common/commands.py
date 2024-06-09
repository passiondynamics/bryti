from pydantic import (
    BaseModel,
    model_validator,
)

from abc import (
    ABC,
    abstractmethod,
)
from datetime import (
    datetime,
    timezone,
)
from inspect import isclass
from typing import List

from src.common.api_interfaces import APIInterfaces
from src.common.state_models import (
    DeathState,
    Permission,
    State,
)


DATETIME_FMT = "%Y-%m-%d @ %-I:%M:%S%P %Z"


class AbstractCommand(ABC):
    def __init__(self, interfaces: APIInterfaces, state: State, permission: Permission):
        self.interfaces = interfaces
        self.state = state
        self.permission = permission

    @abstractmethod
    def execute(self) -> str:
        pass


# --- status ---


class StatusCommand(AbstractCommand):
    """
    Generate a status reply to the ping.
    """

    def execute(self) -> str:
        now = datetime.now(tz=timezone.utc)
        now_str = now.strftime(DATETIME_FMT)
        return f"Ok at {now_str}!"


# --- deaths ---


class AbstractDeathsCommand(AbstractCommand):
    def _generate_reply(self) -> str:
        deaths = self.state.deaths
        reply = "No deaths yet!"
        if deaths is not None and deaths.count != 0:
            timestamp_str = deaths.last_timestamp.strftime(DATETIME_FMT)
            reply = f"Death count: {deaths.count} | Last death: {timestamp_str}"

        return reply


class DeathsInfoCommand(AbstractDeathsCommand):
    """
    Get info about the broadcaster's deaths.
    """

    def execute(self) -> str:
        return self._generate_reply()


class DeathsAddCommand(AbstractDeathsCommand):
    """
    Increment the broadcaster's death count.
    """

    DEDUP_WINDOW_S = 10

    def execute(self) -> str:
        if self.permission < Permission.MODERATOR:
            return "You don't have permissions for that!"

        deaths = self.state.deaths
        now = datetime.now(tz=timezone.utc)
        if deaths is None:
            self.state.deaths = DeathState(count=1, last_timestamp=now)
        elif (now - deaths.last_timestamp).total_seconds() <= self.DEDUP_WINDOW_S:
            return (
                "It's been too soon since they last died! Are you sure they died again?"
            )
        else:
            deaths.count += 1
            deaths.last_timestamp = now

        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


class DeathsSetCommand(AbstractDeathsCommand):
    """
    Set the broadcaster's death count directly.
    """

    def execute(self, deaths: int) -> str:
        if self.permission != Permission.BROADCASTER:
            return "You don't have permissions for that!"

        self.state.deaths = DeathState(
            count=deaths,
            last_timestamp=datetime.now(tz=timezone.utc),
        )

        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


# --- twitch ---


class TwitchConnectCommand(AbstractCommand):
    def execute(self) -> str:
        return "Not implemented yet!"


"""
Tree of available commands. Involves 3 types of key-pairs:
1. <str>: <subclass of AbstractCommand>
   A command, will be called with the remaining args provided.
2. <str>: <dict>
   A command group, with at least one subcommand defined inside.
3. None: <subclass of AbstractCommand>
   A command group's default command (if no args are provided after that group's level).
"""
COMMAND_TREE = {
    "status": StatusCommand,
    "deaths": {
        None: DeathsInfoCommand,
        "add": DeathsAddCommand,
        "set": DeathsSetCommand,
    },
    "twitch": {
        "connect": TwitchConnectCommand,
    },
}
# TODO: add "help" command/dynamically generate help content.


def resolve_command(args: List[str]):
    """
    Look up a command from the command tree using the given args.
    """
    # Make a shallow copy of the list so that we aren't modifying the provided reference.
    args = args.copy()

    # Traverse down the tree.
    curr_node = COMMAND_TREE
    FoundCommandClass = None
    for i in range(len(args)):
        arg = args.pop(0)
        curr_node = curr_node.get(arg)
        if not curr_node:
            # Gave an arg that doesn't exist at this level.
            break
        elif isclass(curr_node) and issubclass(curr_node, AbstractCommand):
            # Leaf node of command tree.
            FoundCommandClass = curr_node
            break
    else:
        # Check if in subcommand group w/ no-arg default.
        FoundCommandClass = curr_node.get(None)

    # Provide remaining args as well to caller.
    return FoundCommandClass, args
