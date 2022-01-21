"""
Revolt API wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Revolt API.

:copyright: (c) 2022 Gael
:license: MIT, see LICENSE for more details.
"""

__title__ = 'pyvolt'
__author__ = 'github.com/Gael-devv'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2022 Gael'
__version__ = '0.1.0a'

from typing import NamedTuple, Literal

from .token import *
from .http import *
from .errors import *
from .file import *
from . import utils


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    release_level: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=0, minor=0, micro=1, release_level='alpha', serial=0)