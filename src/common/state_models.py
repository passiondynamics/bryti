from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
)

from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from typing import (
    Annotated,
    Dict,
    Optional,
)


class Permission(str, Enum):
    EVERYBODY = "everybody"
    MODERATOR = "moderator"
    BROADCASTER = "broadcaster"

    def __lt__(self, other) -> bool:
        members = list(Permission.__members__.values())
        return members.index(self) < members.index(other)

    def __le__(self, other) -> bool:
        members = list(Permission.__members__.values())
        return members.index(self) <= members.index(other)

    def __gt__(self, other) -> bool:
        members = list(Permission.__members__.values())
        return members.index(self) > members.index(other)

    def __ge__(self, other) -> bool:
        members = list(Permission.__members__.values())
        return members.index(self) >= members.index(other)


ISOUTCDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda dt: dt.astimezone(timezone.utc).isoformat(timespec="seconds"),
        return_type=str,
    ),
]


class LookupFields(BaseModel):
    user: str
    twitch_user_id: Optional[str] = None
    discord_user_id: Optional[str] = None
    github_user_id: Optional[str] = None


class CounterState(BaseModel):
    count: int
    last_timestamp: ISOUTCDatetime

    def time_since(self, timestamp) -> str:
        """
        Create a relative time string based off the given timestamp.
        """

        time_since = timestamp - self.last_timestamp
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

        return time_since_str


class State(LookupFields):
    members: Dict[str, Permission] = {}
    deaths: Optional[CounterState] = None
    crimes: Optional[CounterState] = None
    version: int = 0
