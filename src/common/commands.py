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
    CounterState,
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


# --- (general counters) ---


class AbstractCounterCommand(AbstractCommand):
    DEDUP_WINDOW_S = 10
    DENIED_MSG = "You don't have permissions for that!"

    def _generate_reply(self, counter, default_reply, reply_fmt) -> str:
        reply = default_reply
        if counter is not None and counter.count != 0:
            time_since_str = counter.time_since(self.timestamp)
            reply = reply_fmt.format(count=counter.count, time_since=time_since_str)

        return reply

    def _add(self, counter, dedup_msg) -> str | CounterState:
        if self.permission < Permission.MODERATOR:
            return self.DENIED_MSG

        if counter is None:
            return CounterState(count=1, last_timestamp=self.timestamp)

        time_since = self.timestamp - counter.last_timestamp
        time_since_s = time_since.total_seconds()

        if time_since_s <= self.DEDUP_WINDOW_S:
            return dedup_msg

        counter.count += 1
        counter.last_timestamp = self.timestamp
        return counter

    def _set(self, counter, count) -> str | CounterState:
        if self.permission != Permission.BROADCASTER:
            return self.DENIED_MSG

        return CounterState(
            count=count,
            last_timestamp=self.timestamp,
        )


# --- deaths ---


class AbstractDeathsCommand(AbstractCounterCommand):
    def _generate_reply(self) -> str:
        default_reply = "No deaths yet!"
        reply_fmt = "Death count: {count} | Last death: {time_since}"
        reply = super()._generate_reply(self.state.deaths, default_reply, reply_fmt)
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

    def execute(self) -> str:
        dedup_msg = (
            "It's been too soon since they last died! Are you sure they died again?"
        )
        result = self._add(self.state.deaths, dedup_msg)
        if isinstance(result, str):
            return result

        self.state.deaths = result
        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


class DeathsSetCommand(AbstractDeathsCommand):
    """
    Set the broadcaster's death count directly.
    """

    def execute(self, deaths: int) -> str:
        result = self._set(self.state.deaths, deaths)
        if isinstance(result, str):
            return result

        self.state.deaths = result
        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


# --- crimes ---


class AbstractCrimesCommand(AbstractCounterCommand):
    def _generate_reply(self) -> str:
        default_reply = "No crimes yet!"
        reply_fmt = "Crime count: {count} | Last crime: {time_since}"
        reply = super()._generate_reply(self.state.crimes, default_reply, reply_fmt)
        return reply


class CrimesInfoCommand(AbstractCrimesCommand):
    """
    Get info about the broadcaster's crimes.
    """

    def execute(self) -> str:
        return self._generate_reply()


class CrimesAddCommand(AbstractCrimesCommand):
    """
    Increment the broadcaster's crime count.
    """

    def execute(self) -> str:
        dedup_msg = "It's been too soon since they last committed a crime! Did they really commit another?"
        result = self._add(self.state.crimes, dedup_msg)
        if isinstance(result, str):
            return result

        self.state.crimes = result
        self.state = self.interfaces.state_table.update_state(self.state)
        return self._generate_reply()


class CrimesSetCommand(AbstractCrimesCommand):
    """
    Set the broadcaster's crime count directly.
    """

    def execute(self, crimes: int) -> str:
        result = self._set(self.state.crimes, crimes)
        if isinstance(result, str):
            return result

        self.state.crimes = result
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
    # "crimes": {
    #     None: CrimesInfoCommand,
    #     "add": CrimesAddCommand,
    #     "set": CrimesSetCommand,
    # },
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
