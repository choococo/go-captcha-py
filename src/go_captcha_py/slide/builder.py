"""Slide captcha builder, ported from go-captcha/v2/slide/builder.go."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PIL import Image

from .captcha import MODE_BASIC, MODE_DRAG, Captcha
from .options import (
    GraphImage,
    Options,
    Resources,
    with_backgrounds,
    with_graph_images,
)


class Builder:
    """Fluent builder producing slide Captcha instances."""

    def __init__(self, *opts: Callable[[Options], None]) -> None:
        self._options: list[Callable[[Options], None]] = list(opts)
        self._resources: list[Callable[[Resources], None]] = []

    def set_options(self, *opts: Callable[[Options], None]) -> Builder:
        self._options.extend(opts)
        return self

    def set_resources(self, *resources: Callable[[Resources], None]) -> Builder:
        self._resources.extend(resources)
        return self

    def make(self) -> Captcha:
        """Basic-mode slide captcha (fixed Y, slide left→right)."""
        return self._make_with_mode(MODE_BASIC)

    def make_drag_drop(self) -> Captcha:
        """Drag-drop-mode slide captcha (free X/Y drag)."""
        return self._make_with_mode(MODE_DRAG)

    def _make_with_mode(self, mode: int) -> Captcha:
        opts = Options()
        for opt in self._options:
            opt(opts)
        resources = Resources()
        for res in self._resources:
            res(resources)
        return Captcha(mode=mode, opts=opts, resources=resources)


def new_builder(*opts: Callable[[Options], None]) -> Builder:
    """Create a Builder with optional WithXxx option callables."""
    return Builder(*opts)


def _default_graph_images() -> list[GraphImage]:
    from .. import resources as assets

    return [GraphImage(overlay_image=o, shadow_image=s, mask_image=m) for (o, s, m) in assets.get_tiles()]


def make_default_captcha() -> Captcha:
    """Basic-mode slide captcha preloaded with all bundled assets."""
    from .. import resources as assets

    return (
        Builder()
        .set_resources(
            with_graph_images(_default_graph_images()),
            with_backgrounds(list(assets.get_images())),
        )
        .make()
    )


def make_default_drag_drop_captcha() -> Captcha:
    """Drag-drop-mode slide captcha preloaded with all bundled assets."""
    from .. import resources as assets

    return (
        Builder()
        .set_resources(
            with_graph_images(_default_graph_images()),
            with_backgrounds(list(assets.get_images())),
        )
        .make_drag_drop()
    )


def make_captcha(
    backgrounds: Sequence[Image.Image] | None = None,
    graph_images: Sequence[GraphImage] | None = None,
    opts: Sequence[Callable[[Options], None]] = (),
) -> Captcha:
    """Basic-mode slide captcha with custom resources; unspecified parts fall
    back to the bundled assets."""
    from .. import resources as assets

    return (
        Builder(*opts)
        .set_resources(
            with_graph_images(list(graph_images) if graph_images is not None else _default_graph_images()),
            with_backgrounds(list(backgrounds) if backgrounds is not None else list(assets.get_images())),
        )
        .make()
    )


def make_drag_drop_captcha(
    backgrounds: Sequence[Image.Image] | None = None,
    graph_images: Sequence[GraphImage] | None = None,
    opts: Sequence[Callable[[Options], None]] = (),
) -> Captcha:
    """Drag-drop-mode slide captcha with custom resources; unspecified parts
    fall back to the bundled assets."""
    from .. import resources as assets

    return (
        Builder(*opts)
        .set_resources(
            with_graph_images(list(graph_images) if graph_images is not None else _default_graph_images()),
            with_backgrounds(list(backgrounds) if backgrounds is not None else list(assets.get_images())),
        )
        .make_drag_drop()
    )
