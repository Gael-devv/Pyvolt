from enum import Enum

__all__ = (
    "ChannelType",
    "PresenceType",
    "RelationshipType",
    "AssetType",
    "SortType",
)


class ChannelType(Enum):
    saved_message  = "SavedMessage"
    direct_message = "DirectMessage"
    group          = "Group"
    text_channel   = "TextChannel"
    voice_channel  = "VoiceChannel"


class PresenceType(Enum):
    busy      = "Busy"
    idle      = "Idle"
    invisible = "Invisible"
    online    = "Online"


class RelationshipType(Enum):
    blocked                 = "Blocked"
    blocked_other           = "BlockedOther"
    friend                  = "Friend"
    incoming_friend_request = "Incoming"
    none                    = "None"
    outgoing_friend_request = "Outgoing"
    user                    = "User"


class AssetType(Enum):
    image = "Image"
    video = "Video"
    text  = "Text"
    audio = "Audio"
    file  = "File"


class SortType(Enum):
    latest    = "Latest"
    oldest    = "Oldest"
    relevance = "Relevance"