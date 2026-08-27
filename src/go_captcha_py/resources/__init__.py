"""Bundled asset loader — Python equivalent of the go-captcha-assets package.

All resources ship inside the installed package under go_captcha_py/resources/
and are loaded lazily on first access, then cached.

Resources (from https://github.com/wenlng/go-captcha-resources, Apache-2.0):
- images/image-v2-*.jpg   16 main captcha backgrounds
- shapes/shape-*.png      13 shape glyphs (click shape mode)
- thumbs/thumb-*.jpg       5 thumbnail backgrounds
- tiles/tile-N{,-shadow,-mask}.png  4 slide tile graph sets
- fonts/fzshengsksjw_cu.ttf  Chinese font for text mode
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageFont

from .chars import CHINESE_CHARS as _FULL_CHINESE_CHARS

_RES_DIR = Path(__file__).parent

# Small demo seed kept for parity with click/default.go; the default text
# captcha uses the full 3498-char set from chars.py (see get_chinese_chars).
_LEGACY_DEMO_CHARS: list[str] = list("我是行为式验证码的随机文本种子")
# Alphanumeric seeds, ported from go-captcha-assets/bindata/chars
ALPHA_CHARS: list[str] = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
MIXIN_ALPHA_CHARS: list[str] = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

# Default palettes (click/default.go)
COLORS: list[str] = [
    "#fde98e",
    "#60c1ff",
    "#fcb08e",
    "#fb88ff",
    "#b4fed4",
    "#cbfaa9",
    "#78d6f8",
]
THUMB_COLORS: list[str] = [
    "#1f55c4",
    "#780592",
    "#2f6b00",
    "#910000",
    "#864401",
    "#675901",
    "#016e5c",
]
SHADOW_COLOR = "#101010"


def _iter_files(subdir: str, pattern: str) -> list[Path]:
    return sorted((_RES_DIR / subdir).glob(pattern))


@lru_cache(maxsize=1)
def get_chinese_chars() -> tuple[str, ...]:
    """Full Chinese character seed (3498 chars, from upstream char.go)."""
    return _FULL_CHINESE_CHARS


@lru_cache(maxsize=1)
def get_alpha_chars() -> tuple[str, ...]:
    """Plain alphabet seed (upper + lower)."""
    return tuple(ALPHA_CHARS)


@lru_cache(maxsize=1)
def get_mixin_alpha_chars() -> tuple[str, ...]:
    """Alphanumeric seed."""
    return tuple(MIXIN_ALPHA_CHARS)


@lru_cache(maxsize=1)
def get_default_colors() -> tuple[str, ...]:
    """Default main-image dot colors."""
    return tuple(COLORS)


@lru_cache(maxsize=1)
def get_default_thumb_colors() -> tuple[str, ...]:
    """Default thumbnail colors (text + background)."""
    return tuple(THUMB_COLORS)


@lru_cache(maxsize=1)
def get_font(size: int = 40) -> ImageFont.FreeTypeFont:
    """Load the bundled Chinese font (fzshengsksjw_cu)."""
    return ImageFont.truetype(str(_RES_DIR / "fonts" / "fzshengsksjw_cu.ttf"), size)


@lru_cache(maxsize=1)
def get_images() -> tuple[Image.Image, ...]:
    """Main captcha background images (16)."""
    imgs = []
    for path in _iter_files("images", "image-v2-*.jpg"):
        with Image.open(path) as im:
            imgs.append(im.convert("RGB"))
    return tuple(imgs)


@lru_cache(maxsize=1)
def get_shapes() -> dict[str, Image.Image]:
    """Shape glyph images keyed by name (13)."""
    shapes: dict[str, Image.Image] = {}
    for path in _iter_files("shapes", "shape-*.png"):
        with Image.open(path) as im:
            shapes[path.stem] = im.convert("RGBA")
    return shapes


@lru_cache(maxsize=1)
def get_thumbs() -> tuple[Image.Image, ...]:
    """Thumbnail background images (5)."""
    imgs = []
    for path in _iter_files("thumbs", "thumb-*.jpg"):
        with Image.open(path) as im:
            imgs.append(im.convert("RGB"))
    return tuple(imgs)


@lru_cache(maxsize=1)
def get_tiles() -> tuple[tuple[Image.Image, Image.Image, Image.Image], ...]:
    """Slide tile graph sets as (overlay, shadow, mask) tuples (4 sets)."""
    tiles = []
    for path in _iter_files("tiles", "tile-*.png"):
        if not path.stem.startswith("tile-") or len(path.stem.split("-")) != 2:
            continue  # skip tile-N-shadow.png / tile-N-mask.png
        n = path.stem  # tile-1
        shadow_path = path.parent / f"{n}-shadow.png"
        mask_path = path.parent / f"{n}-mask.png"
        with Image.open(path) as overlay, Image.open(shadow_path) as shadow, Image.open(mask_path) as mask:
            tiles.append(
                (
                    overlay.convert("RGBA"),
                    shadow.convert("RGBA"),
                    mask.convert("RGBA"),
                )
            )
    return tuple(tiles)


def clear_cache() -> None:
    """Drop all cached resources (mainly for tests)."""
    for fn in (
        get_chinese_chars,
        get_alpha_chars,
        get_mixin_alpha_chars,
        get_default_colors,
        get_default_thumb_colors,
        get_images,
        get_shapes,
        get_thumbs,
        get_tiles,
    ):
        fn.cache_clear()
