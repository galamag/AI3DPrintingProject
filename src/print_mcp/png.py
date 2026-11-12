"""Writing an RGB PNG from top-down BGRA rows, with the standard library only."""
from __future__ import annotations

import struct
import zlib

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def encode_png(width: int, height: int, bgra: bytes, level: int = 6) -> bytes:
    """Encode `bgra` (4 bytes per pixel, rows top to bottom) as an 8-bit RGB PNG.

    The alpha byte is dropped; every row uses filter type 0.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"image size must be positive, got {width}x{height}")
    if len(bgra) != width * height * 4:
        raise ValueError(f"expected {width * height * 4} bytes for {width}x{height} BGRA, got {len(bgra)}")
    # Reorder channels with slice assignment, which runs in C.
    rgb = bytearray(width * height * 3)
    rgb[0::3] = bgra[2::4]
    rgb[1::3] = bgra[1::4]
    rgb[2::3] = bgra[0::4]
    stride = width * 3
    rows = b"".join(b"\x00" + rgb[row * stride:(row + 1) * stride] for row in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        _SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(rows, level))
        + _chunk(b"IEND", b"")
    )
