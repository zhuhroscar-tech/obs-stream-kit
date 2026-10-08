import struct
import zlib

from obsbuild.mask import corner_alpha, png_bytes


def test_corner_alpha():
    assert corner_alpha(0, 0, 100, 50, 10) == 0
    assert corner_alpha(9, 9, 100, 50, 10) == 255
    assert corner_alpha(50, 25, 100, 50, 10) == 255
    assert corner_alpha(99, 49, 100, 50, 10) == 0


def _alpha_reader(png):
    w, h = struct.unpack(">II", png[16:24])
    i = png.index(b"IDAT")
    n = struct.unpack(">I", png[i - 4:i])[0]
    raw = zlib.decompress(png[i + 4:i + 4 + n])
    stride = 1 + w * 4
    return w, h, (lambda x, y: raw[y * stride + 1 + x * 4 + 3])


def test_png_is_valid_and_has_rounded_corners():
    png = png_bytes(16, 8, 3)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h, alpha = _alpha_reader(png)
    assert (w, h) == (16, 8)
    assert alpha(0, 0) == 0 and alpha(15, 7) == 0 and alpha(8, 4) == 255 and alpha(8, 0) == 255
