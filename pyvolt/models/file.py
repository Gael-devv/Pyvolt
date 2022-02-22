from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Union

import os
import io

__all__ = (
    'File',
)


class File:
    """Respresents a file about to be uploaded to Revolt API"""
    __slots__ = ("fp", "filename", "spoiler")

    if TYPE_CHECKING:
        fp: io.BufferedIOBase
        filename: Optional[str]
        spoiler: bool
    
    def __init__(
        self, 
        fp: Union[str, bytes, os.PathLike, io.BufferedIOBase], 
        filename: Optional[str] = None, 
        *, 
        spoiler: bool = False
    ):
        if isinstance(fp, io.IOBase):
            self.fp = fp
        elif isinstance(fp, bytes):
            self.fp = io.BytesIO(fp)
        else:
            self.fp = open(fp, "rb")

        if filename is None:
            if isinstance(fp, str):
                _, self.filename = os.path.split(fp)
            else:
                self.filename = getattr(fp, "name", None)
        
        if spoiler and self.filename is not None and not self.filename.startswith("SPOILER_"):
            self.filename = "SPOILER_" + self.filename

        self.spoiler = spoiler or (self.filename is not None and self.filename.startswith("SPOILER_"))