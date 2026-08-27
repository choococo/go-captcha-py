"""Click captcha builder, ported from go-captcha/v2/click/builder.go.

Provides NewBuilder-style construction with bundled default resources
(the Python equivalent of the go-captcha-assets package).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PIL import Image

from .captcha import MODE_SHAPE, MODE_TEXT, Captcha
from .options import (
    Options,
    Resources,
    with_backgrounds,
    with_chars,
    with_fonts,
    with_shapes,
    with_thumb_backgrounds,
)


class Builder:
    """Fluent builder producing click Captcha instances."""

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
        """Text-mode captcha with configured options/resources."""
        return self._make_with_mode(MODE_TEXT)

    def make_shape(self) -> Captcha:
        """Shape-mode captcha (graphic click mode)."""
        return self._make_with_mode(MODE_SHAPE)

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


def make_default_text_captcha() -> Captcha:
    """Text-mode captcha preloaded with all bundled assets."""
    from .. import resources as assets

    # NOTE: no with_thumb_backgrounds here — official GoCaptcha thumbnails
    # use a light solid background with dark glyphs; photo backgrounds make
    # small glyphs hard to read (matches upstream default: empty thumb bgs).
    return (
        Builder()
        .set_resources(
            with_chars(assets.get_chinese_chars()),
            with_fonts([assets.get_font(40)]),
            with_backgrounds(list(assets.get_images())),
        )
        .make()
    )


def make_default_shape_captcha() -> Captcha:
    """Shape-mode captcha preloaded with all bundled assets."""
    from .. import resources as assets

    # light solid thumb background (official style, see make_default_text_captcha)
    return (
        Builder()
        .set_resources(
            with_shapes(assets.get_shapes()),
            with_backgrounds(list(assets.get_images())),
        )
        .make_shape()
    )


def make_text_captcha(
    chars: Sequence[str] | None = None,
    fonts: Sequence | None = None,
    backgrounds: Sequence[Image.Image] | None = None,
    thumb_backgrounds: Sequence[Image.Image] | None = None,
    opts: Sequence[Callable[[Options], None]] = (),
) -> Captcha:
    """Text-mode captcha with custom resources; unspecified parts fall back
    to the bundled assets.

    Usage:
        capt = click.make_text_captcha(
            chars=list("春兰秋菊夏竹冬梅"),
            backgrounds=[Image.open("my-bg.jpg")],
        )
    """
    from .. import resources as assets

    # thumb_backgrounds defaults to None (light solid bg, official style);
    # pass photo thumbnails explicitly only if you want them.
    res = [
        with_chars(list(chars) if chars is not None else list(assets.get_chinese_chars())),
        with_fonts(list(fonts) if fonts is not None else [assets.get_font(40)]),
        with_backgrounds(list(backgrounds) if backgrounds is not None else list(assets.get_images())),
    ]
    if thumb_backgrounds is not None:
        res.append(with_thumb_backgrounds(list(thumb_backgrounds)))
    return Builder(*opts).set_resources(*res).make()


def make_shape_captcha(
    shapes: dict[str, Image.Image] | None = None,
    backgrounds: Sequence[Image.Image] | None = None,
    thumb_backgrounds: Sequence[Image.Image] | None = None,
    opts: Sequence[Callable[[Options], None]] = (),
) -> Captcha:
    """Shape-mode captcha with custom resources; unspecified parts fall back
    to the bundled assets."""
    from .. import resources as assets

    res = [
        with_shapes(dict(shapes) if shapes is not None else assets.get_shapes()),
        with_backgrounds(list(backgrounds) if backgrounds is not None else list(assets.get_images())),
    ]
    if thumb_backgrounds is not None:
        res.append(with_thumb_backgrounds(list(thumb_backgrounds)))
    return Builder(*opts).set_resources(*res).make_shape()
