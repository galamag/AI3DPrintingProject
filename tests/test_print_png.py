"""print_mcp.png: writing an RGB PNG from top-down BGRA rows."""
from __future__ import annotations

import struct
import zlib

import pytest

from print_mcp.png import encode_png


def read_png(data: bytes):
    """Minimal reader for the PNGs encode_png writes: returns (width, height, header, rgb rows)."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, chunks = 8, []
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert crc == zlib.crc32(kind + body) & 0xFFFFFFFF
        chunks.append((kind, body))
        pos += 12 + length
    assert chunks[0][0] == b"IHDR" and chunks[-1][0] == b"IEND"
    width, height, depth, colour, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", chunks[0][1]
    )
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    stride = width * 3 + 1
    rows = []
    for row in range(height):
        line = raw[row * stride:(row + 1) * stride]
        assert line[0] == 0, "filter type 0"
        rows.append(line[1:])
    header = (depth, colour, compression, filtering, interlace)
    return width, height, header, rows


def test_two_by_two():
    bgra = bytes([
        1, 2, 3, 255, 4, 5, 6, 255,
        7, 8, 9, 0, 10, 11, 12, 128,
    ])
    data = encode_png(width=2, height=2, bgra=bgra)
    width, height, header, rows = read_png(data)
    assert (width, height) == (2, 2)
    assert header == (8, 2, 0, 0, 0)
    assert rows == [bytes([3, 2, 1, 6, 5, 4]), bytes([9, 8, 7, 12, 11, 10])]


def test_wrong_buffer_length():
    with pytest.raises(ValueError):
        encode_png(width=2, height=2, bgra=bytes(15))


@pytest.mark.parametrize("width, height", [(0, 2), (2, 0), (-1, 2)])
def test_bad_size(width, height):
    with pytest.raises(ValueError):
        encode_png(width=width, height=height, bgra=b"")
