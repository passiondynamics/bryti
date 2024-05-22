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

from src.twitch.notification_models import (
    TwitchChannelChatMessage,
    TwitchStreamOffline,
    TwitchStreamOnline,
)


# --- General request event models. ---


class TwitchEventType(str, Enum):
    CHALLENGE = "webhook_callback_verification"
    NOTIFICATION = "notification"
    REVOCATION = "revocation"


class TwitchHeaders(BaseModel):
    event_id: str = Field(alias="twitch-eventsub-message-id")
    event_type: TwitchEventType = Field(alias="twitch-eventsub-message-type")
    subscription_type: str = Field(alias="twitch-eventsub-subscription-type")
    subscription_version: int = Field(alias="twitch-eventsub-subscription-version")
    timestamp: str = Field(alias="twitch-eventsub-message-timestamp")
    signature: str = Field(alias="twitch-eventsub-message-signature")
    retry_count: int = Field(alias="twitch-eventsub-message-retry")


class TwitchEventSubscriptionCondition(BaseModel):
    broadcaster_user_id: Optional[str] = None
    user_id: Optional[str] = None


#    broadcaster_id: Optional[str]
#    moderator_user_id: Optional[str]
#    from_broadcaster_user_id: Optional[str]
#    to_broadcaster_user_id: Optional[str]
#    reward_id: Optional[str]
#    client_id: Optional[str]
#    conduit_id: Optional[str]
#    organization_id: Optional[str]
#    category_id: Optional[str]
#    campaign_id: Optional[str]
#    extension_client_id: Optional[str]


class TwitchEventSubscriptionTransport(BaseModel):
    method: str
    callback: str


class TwitchEventSubscription(BaseModel):
    id: str
    subscription_type: str = Field(alias="type")
    version: int
    status: str
    cost: int
    condition: TwitchEventSubscriptionCondition
    created_at: str
    transport: TwitchEventSubscriptionTransport


# --- Specific request event models (by TwitchEventType) ---


class TwitchChallengeEvent(BaseModel):
    challenge: str
    subscription: TwitchEventSubscription


class TwitchNotificationEvent(BaseModel):
    subscription: TwitchEventSubscription
    event: TwitchChannelChatMessage | TwitchStreamOffline | TwitchStreamOnline


class TwitchRevocationEvent(BaseModel):
    subscription: TwitchEventSubscription
