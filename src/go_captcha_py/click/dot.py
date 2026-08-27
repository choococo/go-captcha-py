"""Click captcha dot data structures, ported from go-captcha/v2/click/dot.go."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Dot:
    """A single clickable point (character or shape) in the captcha.

    Field names match the Go JSON tags for frontend compatibility.
    """

    index: int = 0
    x: int = 0
    y: int = 0
    size: int = 0
    width: int = 0
    height: int = 0
    text: str = ""
    shape: str = ""
    angle: int = 0
    color: str = ""
    color2: str = ""

    def to_dict(self) -> dict:
        """Serialize with the Go JSON field names."""
        return asdict(self)


@dataclass(slots=True)
class DrawDot:
    """Internal drawing instruction for one dot."""

    dot: Dot
    x: int
    y: int
    font_dpi: int = 72
    text: str = ""
    image: object | None = None  # PIL.Image for shape mode
    use_original_color: bool = False
    size: int = 0
    width: int = 0
    height: int = 0
    angle: int = 0
    color: str = ""
    color2: str = ""
    font: object | None = None  # PIL.ImageFont
    draw_type: int = 0  # 0=text, 1=image


# DrawType constants (click/draw.go)
DRAW_TYPE_STRING = 0
DRAW_TYPE_IMAGE = 1
