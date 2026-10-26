"""Local stand-ins for the node file primitives the log reader needs, for this version of the bot.

DCSServerBot 3.0.5 gives every node ``read_file_window`` and ``list_files``, which also read the files of
an agent. This version has neither, so the log endpoints read the files of the node that serves the
RestAPI only, with these two functions: the same signatures and semantics, a local disk and nothing else.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

__all__ = ["READ_WINDOW_MAX_BYTES", "file_identity", "read_file_window", "list_files"]

#: a window never exceeds this, whatever the caller asks (the 3.0.5 primitive's own ceiling)
READ_WINDOW_MAX_BYTES = 1024 * 1024


def file_identity(st: os.stat_result) -> Any:
    """A value stable across an append and changed by a replacement (creation time on Windows, inode elsewhere)."""
    created = getattr(st, "st_birthtime", None)
    if created:
        return created
    if os.name == "nt":
        return st.st_ctime
    return st.st_ino


async def read_file_window(path: str, *, length: int, offset: int | None = None,
                           behind: int | None = None) -> tuple[bytes, int, Any]:
    """``(window, size, identity)``: the bytes at ``offset``, or the bytes ending at ``behind``."""
    if (offset is None) == (behind is None):
        raise ValueError("read_file_window needs exactly one of 'offset' or 'behind'.")
    length = min(int(length), READ_WINDOW_MAX_BYTES)

    def _read() -> tuple[bytes, int, Any]:
        st = os.stat(path)
        size = st.st_size
        if behind is not None:
            end = max(0, min(int(behind), size))
            start = max(0, end - length)
        else:
            start = min(int(offset), size)
            end = min(size, start + length)
        with open(path, 'rb') as file:
            file.seek(start)
            data = file.read(max(0, end - start))
        return data, size, file_identity(st)

    return await asyncio.to_thread(_read)


async def list_files(path: str, *, pattern: str | list[str] = '*') -> list[tuple[str, int, float]]:
    """The files matching *pattern* in *path* as ``(path, size, mtime)``, newest first; a missing directory is empty."""
    patterns = [pattern] if isinstance(pattern, str) else pattern

    def _list() -> list[tuple[str, int, float]]:
        directory = Path(os.path.expandvars(path))
        found: dict[str, tuple[str, int, float]] = {}
        for pat in patterns:
            for file in directory.glob(pat):
                if file.is_dir():
                    continue
                st = file.stat()
                found[file.as_posix()] = (file.as_posix(), int(st.st_size), float(st.st_mtime))
        return sorted(found.values(), key=lambda entry: entry[2], reverse=True)

    return await asyncio.to_thread(_list)
