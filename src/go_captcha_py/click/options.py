"""Click captcha options and builder, ported from go-captcha/v2/click/{option,resource,builder}.go."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from PIL import Image, ImageFont

# Distort levels re-exported for convenience
from ..base.option import (
    DISTORT_LEVEL_4,
    Point,
    RangeVal,
    Size,
)


@dataclass(slots=True)
class Options:
    """Click captcha configuration (click/option.go)."""

    # main image
    image_size: Size = field(default_factory=lambda: Size(300, 220))
    image_alpha: float = 1.0
    range_len: RangeVal = field(default_factory=lambda: RangeVal(6, 7))
    range_angle_pos: list[RangeVal] = field(
        default_factory=lambda: [
            RangeVal(-15, -8),
            RangeVal(-8, 0),
            RangeVal(0, 8),
            RangeVal(8, 15),
        ]
    )
    range_size: RangeVal = field(default_factory=lambda: RangeVal(26, 32))
    range_colors: list[str] = field(
        default_factory=lambda: [
            "#fde98e",
            "#60c1ff",
            "#fcb08e",
            "#fb88ff",
            "#b4fed4",
            "#cbfaa9",
            "#78d6f8",
        ]
    )
    display_shadow: bool = True
    shadow_color: str = "#101010"
    shadow_point: Point = field(default_factory=lambda: Point(-1, -1))
    use_shape_original_color: bool = False
    font_dpi: int = 72

    # thumbnail
    thumb_image_size: Size = field(default_factory=lambda: Size(150, 40))
    range_verify_len: RangeVal = field(default_factory=lambda: RangeVal(2, 4))
    disabled_range_verify_len: bool = False
    range_thumb_size: RangeVal = field(default_factory=lambda: RangeVal(22, 28))
    range_thumb_colors: list[str] = field(
        default_factory=lambda: [
            "#1f55c4",
            "#780592",
            "#2f6b00",
            "#910000",
            "#864401",
            "#675901",
            "#016e5c",
        ]
    )
    range_thumb_bg_colors: list[str] = field(
        default_factory=lambda: [
            "#1f55c4",
            "#780592",
            "#2f6b00",
            "#910000",
            "#864401",
            "#675901",
            "#016e5c",
        ]
    )
    thumb_bg_distort: int = DISTORT_LEVEL_4
    thumb_bg_circles_num: int = 24
    thumb_bg_slim_line_num: int = 2
    is_thumb_non_deform_ability: bool = True
    # Go's default thumbnail disturbance layer is opaque. This makes the
    # configured circles and slim lines visible behind the target glyphs.
    thumb_disturb_alpha: float = 1.0


@dataclass(slots=True)
class Resources:
    """Click captcha material resources (click/resource.go)."""

    chars: list[str] = field(default_factory=lambda: list("我是行为式验证码的随机文本种子"))
    shapes: list[str] = field(default_factory=list)
    shape_maps: dict[str, Image.Image] = field(default_factory=dict)
    fonts: list[ImageFont.FreeTypeFont] = field(default_factory=list)
    backgrounds: list[Image.Image] = field(default_factory=list)
    thumb_backgrounds: list[Image.Image] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Option callables — mirror the Go WithXxx() functional options
# ---------------------------------------------------------------------------


def with_image_size(size: Size) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.image_size = size

    return opt


def with_image_alpha(alpha: float) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.image_alpha = alpha

    return opt


def with_range_len(val: RangeVal) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_len = val

    return opt


def with_range_angle_pos(vals: Sequence[RangeVal]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_angle_pos = list(vals)

    return opt


def with_range_size(val: RangeVal) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_size = val

    return opt


def with_range_colors(colors: Sequence[str]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_colors = list(colors)

    return opt


def with_display_shadow(val: bool) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.display_shadow = val

    return opt


def with_shadow_color(color: str) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.shadow_color = color

    return opt


def with_shadow_point(point: Point) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.shadow_point = point

    return opt


def with_use_shape_original_color(val: bool) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.use_shape_original_color = val

    return opt


def with_font_dpi(dpi: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.font_dpi = dpi

    return opt


def with_thumb_image_size(size: Size) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.thumb_image_size = size

    return opt


def with_range_verify_len(val: RangeVal) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_verify_len = val

    return opt


def with_disabled_range_verify_len(val: bool) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.disabled_range_verify_len = val

    return opt


def with_range_thumb_size(val: RangeVal) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_thumb_size = val

    return opt


def with_range_thumb_colors(colors: Sequence[str]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_thumb_colors = list(colors)

    return opt


def with_range_thumb_bg_colors(colors: Sequence[str]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_thumb_bg_colors = list(colors)

    return opt


def with_thumb_bg_distort(level: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.thumb_bg_distort = level

    return opt


def with_thumb_bg_circles_num(num: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.thumb_bg_circles_num = num

    return opt


def with_thumb_bg_slim_line_num(num: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.thumb_bg_slim_line_num = num

    return opt


def with_is_thumb_non_deform_ability(val: bool) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.is_thumb_non_deform_ability = val

    return opt


# ---------------------------------------------------------------------------
# Resource callables — mirror the Go WithXxx() resource setters
# ---------------------------------------------------------------------------


def with_chars(chars: Sequence[str]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.chars = list(chars)

    return res


def with_shapes(shape_maps: dict[str, Image.Image]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.shape_maps = dict(shape_maps)
        r.shapes = list(shape_maps.keys())

    return res


def with_fonts(fonts: Sequence[ImageFont.FreeTypeFont]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.fonts = list(fonts)

    return res


def with_backgrounds(images: Sequence[Image.Image]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.backgrounds = list(images)

    return res


def with_thumb_backgrounds(images: Sequence[Image.Image]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.thumb_backgrounds = list(images)

    return res


def default_options() -> Options:
    """Fresh copy of the default options (click/default.go)."""
    return Options()
