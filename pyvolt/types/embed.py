from typing import Literal, TypedDict, Union


class _BaseEmbed(TypedDict):
    icon_url: str
    url: str
    
    title: str
    description: str
    colour: str


class TextEmbed(_BaseEmbed):
    type: Literal["Text"]
    media: str


class _EmbedSpecial(TypedDict):
    type: None


class _EmbedImage(TypedDict, total=False):
    url: str
    width: int
    height: int
    size: str


class _EmbedVideo(TypedDict, total=False):
    url: str
    width: int
    height: int


class WebsiteEmbed(_BaseEmbed):
    type: Literal["Website"]
    special: _EmbedSpecial
    image: _EmbedImage
    video: _EmbedVideo
    
    site_name: str


EmbedType = Union(TextEmbed, WebsiteEmbed)

"""
# text embed
{
    "type": "Text",
    "icon_url": "string",
    "url": "string",
    "title": "string",
    "description": "string",
    "media": "string",
    "colour": "string"
}

# website embed
{
    "type": "Website",
    "url": "string",
    "special": {
        "type": "None"
    },
    "title": "string",
    "description": "string",
    "image": {
        "url": "string",
        "width": 0,
        "height": 0,
        "size": "Large"
    },
    "video": {
        "url": "string",
        "width": 0,
        "height": 0
    },
    "site_name": "string",
    "icon_url": "string",
    "colour": "string"
}
"""
