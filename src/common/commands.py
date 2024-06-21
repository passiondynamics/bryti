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
        self.timestamp = datetime.now(tz=timezone.utc)

    @abstractmethod
    def execute(self) -> str:
        pass


# --- status ---


class StatusCommand(AbstractCommand):
    """
    Generate a status reply to the ping.
    """

    def execute(self) -> str:
        timestamp_str = self.timestamp.strftime(DATETIME_FMT)
        return f"Ok at {timestamp_str}!"


# --- deaths ---


class AbstractDeathsCommand(AbstractCommand):
    def _generate_reply(self) -> str:
        deaths = self.state.deaths
        reply = "No deaths yet!"
        if deaths is not None and deaths.count != 0:
            # Create a relative time string.
            time_since = self.timestamp - deaths.last_timestamp
            s = time_since.seconds % 60
            m = time_since.seconds // 60 % 60
            h = time_since.seconds // 3600
            d = time_since.days

            # Consecutive conditions to prevent "0"s from being shown.
            time_since_str = ""
            if s > 0:
                time_since_str = f"{s}s{time_since_str}"
            if m > 0:
                time_since_str = f"{m}m{time_since_str}"
            if h > 0:
                time_since_str = f"{h}h{time_since_str}"
            if d > 0:
                time_since_str = f"{d}d{time_since_str}"
            if time_since_str:
                time_since_str += " ago"
            else:
                time_since_str = "just now"

            reply = f"Death count: {deaths.count} | Last death: {time_since_str}"

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
        if deaths is None:
            self.state.deaths = DeathState(count=1, last_timestamp=self.timestamp)
        elif (
            self.timestamp - deaths.last_timestamp
        ).total_seconds() <= self.DEDUP_WINDOW_S:
            return (
                "It's been too soon since they last died! Are you sure they died again?"
            )
        else:
            deaths.count += 1
            deaths.last_timestamp = self.timestamp

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
            last_timestamp=self.timestamp,
        )

        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


# --- twitch ---


class TwitchConnectCommand(AbstractCommand):
    def execute(self) -> str:
        # TODO: generate URL for access.
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
