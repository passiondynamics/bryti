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


class DeathState(BaseModel):
    count: int
    last_timestamp: ISOUTCDatetime


class State(BaseModel):
    user: str
    twitch_username: Optional[str] = None
    discord_username: Optional[str] = None
    members: Dict[str, Permission] = {}
    deaths: Optional[DeathState] = None
    version: int = 0
