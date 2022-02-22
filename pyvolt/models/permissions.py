from __future__ import annotations

from .flags import BaseFlags, flag_value, fill_with_flags

__all__ = (
    "ChannelPermissions",
    "ServerPermissions"
)

# Channel permissions
#
#   View = 0b00000000000000000000000000000001           // 1
#   SendMessage = 0b00000000000000000000000000000010    // 2
#   ManageMessages = 0b00000000000000000000000000000100 // 4
#   ManageChannel = 0b00000000000000000000000000001000  // 8
#   VoiceCall = 0b00000000000000000000000000010000      // 16
#   InviteOthers = 0b00000000000000000000000000100000   // 32
#   EmbedLinks = 0b00000000000000000000000001000000     // 64
#   UploadFiles = 0b00000000000000000000000010000000    // 128


# Server permissions
#
#   View = 0b00000000000000000000000000000001            // 1
#   ManageRoles = 0b00000000000000000000000000000010     // 2
#   ManageChannels = 0b00000000000000000000000000000100  // 4
#   ManageServer = 0b00000000000000000000000000001000    // 8
#   KickMembers = 0b00000000000000000000000000010000     // 16
#   BanMembers = 0b00000000000000000000000000100000      // 32

#   ChangeNickname = 0b00000000000000000001000000000000  // 4096
#   ManageNicknames = 0b00000000000000000010000000000000 // 8192
#   ChangeAvatar = 0b00000000000000000100000000000000    // 16382
#   RemoveAvatars = 0b00000000000000001000000000000000   // 32768

@fill_with_flags()
class ChannelPermissions(BaseFlags):
    """Represents the channel permissions for a role as seen in channel settings."""

    __slots__ = ()

    def __init__(self, permissions: int = 0, **kwargs: bool):
        if not isinstance(permissions, int):
            raise TypeError(f"Expected int parameter, received {permissions.__class__.__name__} instead.")

        self.value = permissions
        
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid permission name.")
        
            setattr(self, key, value)

    @classmethod
    def none(cls) -> ChannelPermissions:
        """A factory method that creates a :class:`ChannelPermissions` with all
        permissions set to ``False``.
        """
        return cls(0)

    @classmethod
    def all(cls) -> ChannelPermissions:
        """A factory method that creates a :class:`ChannelPermissions` with all
        permissions set to ``True``.
        """
        return cls(0b11111011)

    @classmethod
    def text(cls) -> ChannelPermissions:
        """A factory method that creates a :class:`ChannelPermissions` with all
        "Text" channel permissions from the Revolt api set to ``True``.
        """
        return cls(0b11000011)

    @flag_value
    def view_channel(self) -> int:
        return 1 << 0

    @flag_value
    def send_message(self) -> int:
        return 1 << 1
    
    @flag_value
    def manage_messages(self) -> int:
        return 1 << 2 

    @flag_value
    def manage_channel(self) -> int:
        return 1 << 3

    @flag_value
    def connect(self) -> int:
        return 1 << 4

    @flag_value
    def invite_others(self) -> int:
        return 1 << 5

    @flag_value
    def embed_links(self) -> int:
        return 1 << 6

    @flag_value
    def upload_files(self) -> int:
        return 1 << 7


@fill_with_flags()
class ServerPermissions(BaseFlags):
    """Represents the server permissions for a role as seen in server settings."""

    __slots__ = ()

    def __init__(self, permissions: int = 0, **kwargs: bool):
        if not isinstance(permissions, int):
            raise TypeError(f"Expected int parameter, received {permissions.__class__.__name__} instead.")

        self.value = permissions
        
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid permission name.")
        
            setattr(self, key, value)

    @classmethod
    def none(cls) -> ServerPermissions:
        return cls(0)

    @classmethod
    def all(cls) -> ServerPermissions:
        return cls(0b1111000000111111)

    @classmethod
    def moderator(cls) -> ServerPermissions:
        return cls(0b1111000000101111)

    @flag_value
    def view_server(self) -> int:
        return 1 << 0

    @flag_value
    def manage_roles(self) -> int:
        return 1 << 1

    @flag_value
    def manage_channels(self) -> int:
        return 1 << 2

    @flag_value
    def manage_server(self) -> int:
        return 1 << 3

    @flag_value
    def kick_members(self) -> int:
        return 1 << 4

    @flag_value
    def ban_members(self) -> int:
        return 1 << 5

    @flag_value
    def change_nicknames(self) -> int:
        return 1 << 12

    @flag_value
    def manage_nicknames(self) -> int:
        return 1 << 13

    @flag_value
    def change_avatar(self) -> int:
        return 1 << 14

    @flag_value
    def remove_avatars(self) -> int:
        return 1 << 15
