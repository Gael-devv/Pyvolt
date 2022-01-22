from typing import Literal, TypedDict, Union


class _Embed(TypedDict):
    type: Literal['Text', 'Website']
    icon_url: str
    url: str
    
    title: str
    description: str
    
    colour: str


class TextEmbed(_Embed):
    media: str


class _EmbedSpecialOptional(TypedDict):
    type: None


class _EmbedImageOptional(TypedDict):
    url: str
    width: int
    height: int
    size: str


class _EmbedVideoOptional(TypedDict):
    url: str
    width: int
    height: int


class WebsiteEmbed(_Embed):
    special: _EmbedSpecialOptional
    image: _EmbedImageOptional
    video: _EmbedVideoOptional
    
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
