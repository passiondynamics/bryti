from pydantic import (
    BaseModel,
    Field,
)

from enum import Enum
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
)

from src.twitch.event_models import (
    TwitchChannelChatMessage,
    TwitchChannelUpdate,
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
    broadcaster_user_id: Optional[str]
    user_id: Optional[str]


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
    callback: Optional[str]


class TwitchEventSubscription(BaseModel):
    subscription_id: str = Field(alias="id")
    subscription_type: str = Field(alias="type")
    version: str
    status: str
    cost: int
    condition: TwitchEventSubscriptionCondition
    created_at: str
    transport: TwitchEventSubscriptionTransport


# --- Specific request event models (by TwitchEventType) ---

class TwitchChallengeBody(BaseModel):
    challenge: str
    subscription: TwitchEventSubscription


class TwitchNotificationBody(BaseModel):
    subscription: TwitchEventSubscription
    event: TwitchChannelUpdate | TwitchChannelChatMessage


class TwitchRevocationBody(BaseModel):
    subscription: TwitchEventSubscription


# --- General API response models ---

# fmt: off
T = TypeVar("T")
class TwitchResponse(BaseModel, Generic[T]):
    data: T
    total: int
    total_cost: int
    max_total_cost: int

# fmt: on
