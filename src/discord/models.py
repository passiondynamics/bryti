from pydantic import (
    BaseModel,
    Field,
)

from enum import Enum
from typing import (
    Any,
    Generic,
    List,
    Optional,
    TypeVar,
)


class DiscordHeaders(BaseModel):
    signature: str = Field(alias="x-signature-ed25519")
    timestamp: str = Field(alias="x-signature-timestamp")


class DiscordEventType(int, Enum):
    PING = 1
    APPLICATION_COMMAND = 2


class DiscordEvent(BaseModel):
    event_type: str = Field(alias="type")
