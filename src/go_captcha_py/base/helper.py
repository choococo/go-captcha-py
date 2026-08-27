"""Color / image helpers, ported from go-captcha/v2/base/helper."""

from __future__ import annotations

from PIL import Image

_HEX_COLOR_RE = None


def parse_hex_color(hex_color: str) -> tuple[int, int, int, int] | None:
    """Parse '#rrggbb' / '#rrggbbaa' into an (r, g, b, a) 0-255 tuple, None on failure."""
    if not hex_color:
        return None
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) not in (6, 8):
        return None
    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        a = int(value[6:8], 16) if len(value) == 8 else 255
    except ValueError:
        return None
    return r, g, b, a


def to_hex_color(r: int, g: int, b: int, a: int = 255) -> str:
    """Format an RGBA 0-255 tuple as '#rrggbb(aa)'."""
    if a >= 255:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


def create_nrgba_canvas(width: int, height: int, transparent: bool = True) -> Image.Image:
    """Create an RGBA canvas; transparent or opaque white."""
    if transparent:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))
    return Image.new("RGBA", (width, height), (255, 255, 255, 255))


def tint_image(img: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    """Colorize an image's alpha shape with a solid color, keeping the alpha mask.

    Mirrors Go's palette-based recoloring of shape images: every opaque pixel
    becomes `color`, transparent pixels stay transparent.
    """
    src = img.convert("RGBA")
    solid = Image.new("RGBA", src.size, color)
    return Image.composite(solid, Image.new("RGBA", src.size, (0, 0, 0, 0)), src.split()[3])


def paste_over(
    dst: Image.Image,
    src: Image.Image,
    xy: tuple[int, int],
    src_box: tuple[int, int, int, int] | None = None,
) -> None:
    """Alpha-composite `src` (optionally a sub-region) onto `dst` at `xy`, in place."""
    region = src if src_box is None else src.crop(src_box)
    if region.mode != "RGBA":
        region = region.convert("RGBA")
    dst.alpha_composite(region, dest=xy)


def calc_margin_blank_area(img: Image.Image) -> tuple[int, int, int, int]:
    """Return the (min_x, min_y, max_x, max_y) bounding box of non-blank pixels.

    Mirrors canvas.NRGBA.CalcMarginBlankArea. Falls back to full bounds on an
    entirely blank image.
    """
    alpha = img.split()[3]
    bbox = alpha.getbbox()
    if bbox is None:
        return 0, 0, img.size[0], img.size[1]
    return bbox[0], bbox[1], bbox[2], bbox[3]
