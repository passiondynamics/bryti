from pydantic import (
    BaseModel,
    Field,
)

from enum import Enum


class TwitchEventType(str, Enum):
    CHALLENGE = "webhook_callback_verification"
    NOTIFICATION = "notification"
    REVOCATION = "revocation"


class TwitchHeaders(BaseModel):
    event_type: TwitchEventType = Field(alias="twitch-eventsub-message-type")


class TwitchChallengeBody(BaseModel):
    challenge: str
