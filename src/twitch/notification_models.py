from pydantic import (
    BaseModel,
    Field,
)

from typing import (
    List,
    Optional,
)

# --- channel.chat.message ---


class TwitchCheermote(BaseModel):
    prefix: str
    bits: int
    tier: int


class TwitchEmote(BaseModel):
    id: str
    emote_set_id: str
    owner_id: str
    emote_format: str = Field(alias="format")


class TwitchMention(BaseModel):
    user_id: str
    user_name: str
    user_login: str


class TwitchMessageFragment(BaseModel):
    fragment_type: str = Field(alias="type")
    text: str
    cheermote: Optional[TwitchCheermote] = None
    emote: Optional[TwitchEmote] = None
    mention: Optional[TwitchMention] = None


class TwitchMessage(BaseModel):
    text: str
    fragments: List[TwitchMessageFragment]


class TwitchBadges(BaseModel):
    set_id: str
    id: str
    info: str


class TwitchCheer(BaseModel):
    bits: int


class TwitchReply(BaseModel):
    parent_message_id: str
    parent_message_body: str
    parent_user_id: str
    parent_user_name: str
    parent_user_login: str
    thread_message_id: str
    thread_user_id: str
    thread_user_name: str
    thread_user_login: str


class TwitchChannelChatMessage(BaseModel):
    broadcaster_user_id: str
    broadcaster_user_name: str
    broadcaster_user_login: str
    chatter_user_id: str
    chatter_user_name: str
    chatter_user_login: str
    message_id: str
    message: TwitchMessage
    message_type: str
    badges: List[TwitchBadges]
    cheer: Optional[TwitchCheer] = None
    color: str
    reply: Optional[TwitchReply] = None
    channel_points_custom_reward_id: Optional[str] = None


# --- stream.online ---


class TwitchStreamOnline(BaseModel):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    id: str
    stream_type: str = Field(alias="type")
    started_at: str


# --- stream.offline ---


class TwitchStreamOffline(BaseModel):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
