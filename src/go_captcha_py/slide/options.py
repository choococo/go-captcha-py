"""Slide captcha options, ported from go-captcha/v2/slide/{option,resource}.go."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from PIL import Image

from ..base.option import RangeVal, Size

# Dead-zone directions (slide/option.go DeadZoneDirectionType)
DEAD_ZONE_DIRECTION_TOP = 0
DEAD_ZONE_DIRECTION_RIGHT = 1
DEAD_ZONE_DIRECTION_BOTTOM = 2
DEAD_ZONE_DIRECTION_LEFT = 3


@dataclass(slots=True)
class GraphImage:
    """A slide tile graph set: overlay (tile), shadow (notch shadow), mask (cut mask)."""

    overlay_image: Image.Image
    shadow_image: Image.Image
    mask_image: Image.Image


@dataclass(slots=True)
class Options:
    """Slide captcha configuration (slide/option.go)."""

    image_size: Size = field(default_factory=lambda: Size(300, 220))
    image_alpha: float = 1.0
    range_dead_zone_directions: list[int] = field(
        default_factory=lambda: [
            DEAD_ZONE_DIRECTION_LEFT,
            DEAD_ZONE_DIRECTION_RIGHT,
            DEAD_ZONE_DIRECTION_BOTTOM,
            DEAD_ZONE_DIRECTION_TOP,
            3,
        ]
    )
    gen_graph_number: int = 1
    range_graph_angle_pos: list[RangeVal] = field(default_factory=lambda: [RangeVal(0, 0)])
    range_graph_size: RangeVal = field(default_factory=lambda: RangeVal(60, 70))
    enable_graph_vertical_random: bool = False


@dataclass(slots=True)
class Resources:
    """Slide captcha material resources (slide/resource.go)."""

    backgrounds: list[Image.Image] = field(default_factory=list)
    graph_images: list[GraphImage] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Option callables
# ---------------------------------------------------------------------------


def with_image_size(size: Size) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.image_size = size

    return opt


def with_image_alpha(alpha: float) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.image_alpha = alpha

    return opt


def with_range_dead_zone_directions(directions: Sequence[int]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_dead_zone_directions = list(directions)

    return opt


def with_gen_graph_number(val: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.gen_graph_number = val

    return opt


def with_range_graph_angle_pos(vals: Sequence[RangeVal]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_graph_angle_pos = list(vals)

    return opt


def with_range_graph_size(val: RangeVal) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_graph_size = val

    return opt


def with_enable_graph_vertical_random(val: bool) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.enable_graph_vertical_random = val

    return opt


# ---------------------------------------------------------------------------
# Resource callables
# ---------------------------------------------------------------------------


def with_backgrounds(images: Sequence[Image.Image]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.backgrounds = list(images)

    return res


def with_graph_images(graphs: Sequence[GraphImage]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.graph_images = list(graphs)

    return res


def default_options() -> Options:
    """Fresh copy of the default options (slide/default.go)."""
    return Options()
