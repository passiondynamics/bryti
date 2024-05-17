from pydantic import (
    BaseModel,
    Field,
)

from typing import (
    List,
    Optional,
)

# --- channel.chat.message ---


class TwitchCheermote:
    prefix: str
    bits: int
    tier: int


class TwitchEmote:
    emote_id: str = Field(alias="id")
    emote_set_id: str
    owner_id: str
    emote_format: str = Field(alias="format")


class TwitchMention:
    user_id: str
    user_name: str
    user_login: str


class TwitchMessageFragment:
    fragment_type: str = Field(alias="type")
    text: str
    cheermote: Optional[TwitchCheermote]
    emote: Optional[TwitchEmote]
    mention: Optional[TwitchMention]


class TwitchMessage:
    text: str
    fragments: List[TwitchMessageFragment]


class TwitchBadges:
    set_id: str
    badge_id: str = Field(alias="id")
    info: str


class TwitchCheer:
    bits: int


class TwitchReply:
    parent_message_id: str
    parent_message_body: str
    parent_user_id: str
    parent_user_name: str
    parent_user_login: str
    thread_message_id: str
    thread_user_id: str
    thread_user_name: str
    thread_user_login: str


class TwitchChannelChatMessage:
    broadcaster_user_id: str
    broadcaster_user_name: str
    broadcaster_user_login: str
    chatter_user_id: str
    chatter_user_name: str
    chatter_user_login: str
    message_id: str
    message: List[TwitchMessage]
    message_type: str
    badges: List[TwitchBadges]
    cheer: Optional[TwitchCheer]
    color: str
    reply: Optional[TwitchReply]
    channel_points_custom_reward_id: Optional[str]


# --- channel.update ---


class TwitchChannelUpdate:
    pass
