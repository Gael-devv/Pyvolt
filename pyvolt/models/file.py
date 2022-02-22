"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
Copyright (c) 2022 Gael

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
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