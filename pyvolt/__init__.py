"""
Revolt API wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Revolt API.

:copyright: (c) 2022 Gael
:license: MIT, see LICENSE for more details.
"""

__title__ = "pyvolt"
__author__ = "github.com/Gael-devv"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2022 Gael"
__version__ = "0.2.0a"

from typing import NamedTuple, Literal

from .client import *
from .errors import *

from .models.asset import *
from .models.embeds import *
from .models.file import *
from .models.flags import *
from .models.message import *
from .models.permissions import *
from .models.role import *
from .models.token import *
from . import utils


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    release_level: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=0, minor=2, micro=0, release_level="alpha", serial=0)