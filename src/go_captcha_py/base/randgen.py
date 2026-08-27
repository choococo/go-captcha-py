"""Random generation helpers, ported from go-captcha/v2/base/randgen + base/random."""

from __future__ import annotations

import random as _random
import re
from collections.abc import Sequence

from PIL import Image

_CHINESE_RE = re.compile(r"[一-龥]")


def rand_int(min_val: int, max_val: int) -> int:
    """Random int in [min_val, max_val) — mirrors Go's RandInt."""
    if max_val <= min_val:
        return min_val
    return _random.randint(min_val, max_val - 1)


def rand_int_fast(min_val: int, max_val: int) -> int:
    """Random int in [min_val, max_val] inclusive — mirrors Go's RandIntFast."""
    if max_val < min_val:
        return min_val
    return _random.randint(min_val, max_val)


def rand_index(length: int) -> int:
    """Random index into a slice of `length`, -1 if empty — mirrors helper.RandIndex."""
    if length <= 0:
        return -1
    return _random.randint(0, length - 1)


def perm(n: int) -> list[int]:
    """Random permutation of range(n) — mirrors random.Perm."""
    return _random.sample(range(n), n)


def rand_string(chars: Sequence[str]) -> str:
    """Random element from chars, '' if empty."""
    if not chars:
        return ""
    return chars[_random.randint(0, len(chars) - 1)]


def rand_font(fonts: Sequence) -> object | None:
    """Random font (FreeTypeFont) from a list."""
    index = rand_index(len(fonts))
    if index < 0:
        return None
    return fonts[index]


def rand_hex_color(colors: Sequence[str]) -> str:
    """Random hex color string from a list."""
    index = rand_index(len(colors))
    if index < 0:
        return ""
    return colors[index]


def rand_image(images: Sequence[Image.Image]) -> Image.Image | None:
    """Random image from a list."""
    index = rand_index(len(images))
    if index < 0:
        return None
    return images[index]


def rand_cut_image_pos(width: int, height: int, img: Image.Image) -> tuple[int, int]:
    """Random crop offset so a width x height view fits inside img — mirrors RangCutImagePos."""
    i_w, i_h = img.size
    cur_x = 0
    cur_y = 0
    if i_w - width > 0:
        cur_x = _random.randint(0, i_w - width)
    if i_h - height > 0:
        cur_y = _random.randint(0, i_h - height)
    return cur_x, cur_y


def is_chinese_char(text: str) -> bool:
    """True if the text contains Chinese characters."""
    if not text:
        return False
    return bool(_CHINESE_RE.search(text))


def len_chinese_char(text: str) -> int:
    """Character count as Go's helper.LenChineseChar: rune length for CJK, else byte-ish length."""
    return len(text)


def format_alpha(alpha: float) -> int:
    """Format a 0..1 float alpha into a 0..255 byte — mirrors helper.FormatAlpha."""
    if alpha <= 0:
        return 0
    if alpha >= 1:
        return 255
    return round(alpha * 255)
