"""Rotate captcha module, ported from go-captcha/v2/rotate.

Users rotate a circular thumbnail to align with the master image's angle.

Usage:
    from go_captcha_py import rotate

    capt = rotate.make_default_captcha()
    data = capt.generate()
    block = data.get_data()                     # server-side answer (angle ...)
    b64 = data.get_master_image().to_base64()   # send to frontend

    ok = rotate.validate(src_angle, angle, padding)
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field

from PIL import Image, ImageDraw

from ..base.imagedata import PNGImageData
from ..base.option import RangeVal
from ..base.randgen import rand_cut_image_pos, rand_image, rand_index, rand_int_fast


class CaptchaError(Exception):
    """Rotate captcha generation error."""


EMPTY_IMAGE_ERR = "no image"
IMAGE_TYPE_ERR = "image must be of type image.Image"


@dataclass(slots=True)
class Block:
    """Rotate captcha verification data (rotate/block.go).

    parent_width/parent_height deprecated but kept for JSON parity.
    """

    parent_width: int = 0
    parent_height: int = 0
    width: int = 0
    height: int = 0
    angle: int = 0

    def to_dict(self) -> dict:
        """Serialize with the Go JSON field names."""
        return asdict(self)


@dataclass(slots=True)
class Options:
    """Rotate captcha configuration (rotate/option.go + default.go)."""

    image_square_size: int = 220
    range_angle_pos: list[RangeVal] = field(default_factory=lambda: [RangeVal(30, 330)])
    thumb_image_alpha: float = 1.0
    range_thumb_image_square_size: list[int] = field(default_factory=lambda: [140, 150, 160, 170])


@dataclass(slots=True)
class Resources:
    """Rotate captcha material resources."""

    images: list[Image.Image] = field(default_factory=list)


def with_image_square_size(val: int) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.image_square_size = val

    return opt


def with_range_angle_pos(vals: Sequence[RangeVal]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_angle_pos = list(vals)

    return opt


def with_thumb_image_alpha(val: float) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.thumb_image_alpha = val

    return opt


def with_range_thumb_image_square_size(vals: Sequence[int]) -> Callable[[Options], None]:
    def opt(o: Options) -> None:
        o.range_thumb_image_square_size = list(vals)

    return opt


def with_images(images: Sequence[Image.Image]) -> Callable[[Resources], None]:
    def res(r: Resources) -> None:
        r.images = list(images)

    return res


def validate(src_angle: int, angle: int, padding: int) -> bool:
    """Check whether the user's rotation angle matches the target.

    Mirrors rotate.Validate.
    """
    new_angle = padding * 2
    new_angle_ = angle - padding
    return src_angle >= new_angle_ and src_angle <= new_angle_ + new_angle


@dataclass(slots=True)
class CaptchaData:
    """Generated rotate captcha: block + master image + thumb image."""

    block: Block
    master_image: PNGImageData
    thumb_image: PNGImageData

    def get_data(self) -> Block:
        """Verification block (kept server-side)."""
        return self.block

    def get_master_image(self) -> PNGImageData:
        """Circular master image (upright)."""
        return self.master_image

    def get_thumb_image(self) -> PNGImageData:
        """Circular rotated thumbnail the user must align."""
        return self.thumb_image


class _DrawImage:
    """Rotate drawing implementation (rotate/draw.go)."""

    @staticmethod
    def _circle_mask(size: int) -> Image.Image:
        """L mask with a filled circle of radius size/2."""
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size - 1, size - 1), fill=255)
        return mask

    def draw_with_nrgba(self, square_size: int, background: Image.Image) -> Image.Image:
        """Crop a square from the background, cut to a circle.

        Mirrors DrawWithNRGBA.
        """
        rcm = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
        bg = background.convert("RGB")
        cx, cy = rand_cut_image_pos(square_size, square_size, bg)
        region = bg.crop((cx, cy, cx + square_size, cy + square_size))
        rcm.paste(region, (0, 0))
        mask = self._circle_mask(square_size)
        out = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
        out.paste(rcm, (0, 0), mask)
        return out

    def draw_with_crop_circle(
        self,
        background: Image.Image,
        square_size: int,
        rotate_deg: int,
        scale_ratio_size: int,
        alpha: float,
    ) -> Image.Image:
        """Circle-crop the master, shrink by scale_ratio_size, rotate by angle.

        Mirrors DrawWithCropCircle: crop a centered circle of the smaller
        dimension, scale down, rotate with expand, then crop back to size.
        """
        cvs = background.copy()
        if cvs.mode != "RGBA":
            cvs = cvs.convert("RGBA")

        # circle crop of the master image at full size
        mask_full = self._circle_mask(min(cvs.size))
        circle = Image.new("RGBA", cvs.size, (0, 0, 0, 0))
        circle.paste(cvs, (0, 0), mask_full)

        # scale down by scale_ratio_size (the ring width between master and thumb)
        thumb_size = min(cvs.size) - scale_ratio_size * 2
        if thumb_size <= 0:
            thumb_size = min(cvs.size)
        thumb = circle.resize((thumb_size, thumb_size), Image.BICUBIC)

        # rotate by the target angle
        thumb = thumb.rotate(rotate_deg, resample=Image.BICUBIC, expand=False)

        # alpha option
        if alpha < 1:
            a = thumb.split()[3].point(lambda v: int(v * alpha))
            thumb.putalpha(a)

        return thumb


class Captcha:
    """Rotate captcha implementation (rotate/rotate.go)."""

    def __init__(self, opts: Options | None = None, resources: Resources | None = None) -> None:
        self.opts = opts if opts is not None else Options()
        self.resources = resources if resources is not None else Resources()
        self._draw = _DrawImage()

    def generate(self) -> CaptchaData:
        """Generate a rotate captcha. Raises CaptchaError on invalid config."""
        self._check()

        thumb_size = self._rand_thumb_image_square_size()
        block = self._gen_block(self.opts.image_square_size, thumb_size)

        master = self._draw.draw_with_nrgba(self.opts.image_square_size, rand_image(self.resources.images))
        thumb = self._draw.draw_with_crop_circle(
            master,
            square_size=thumb_size,
            rotate_deg=block.angle,
            scale_ratio_size=(self.opts.image_square_size - thumb_size) // 2,
            alpha=self.opts.thumb_image_alpha,
        )

        return CaptchaData(
            block=block,
            master_image=PNGImageData(master),
            thumb_image=PNGImageData(thumb),
        )

    def _rand_angle(self) -> int:
        angles = self.opts.range_angle_pos
        index = rand_index(len(angles))
        if index < 0:
            return 0
        angle = angles[index]
        return rand_int_fast(angle.min, angle.max)

    def _rand_thumb_image_square_size(self) -> int:
        sizes = self.opts.range_thumb_image_square_size
        index = rand_index(len(sizes))
        if index < 0:
            return 150
        return sizes[index]

    def _gen_block(self, image_size: int, thumb_size: int) -> Block:
        return Block(
            angle=self._rand_angle(),
            width=thumb_size,
            height=thumb_size,
            parent_width=image_size,
            parent_height=image_size,
        )

    def _check(self) -> None:
        if not self.resources.images:
            raise CaptchaError(EMPTY_IMAGE_ERR)
        for img in self.resources.images:
            if img is None:
                raise CaptchaError(IMAGE_TYPE_ERR)


class Builder:
    """Fluent builder producing rotate Captcha instances."""

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
        opts = Options()
        for opt in self._options:
            opt(opts)
        resources = Resources()
        for res in self._resources:
            res(resources)
        return Captcha(opts=opts, resources=resources)


def new_builder(*opts: Callable[[Options], None]) -> Builder:
    """Create a Builder with optional WithXxx option callables."""
    return Builder(*opts)


def make_default_captcha() -> Captcha:
    """Rotate captcha preloaded with all bundled assets."""
    from .. import resources as assets

    return Builder().set_resources(with_images(list(assets.get_images()))).make()


def make_captcha(
    images: Sequence[Image.Image] | None = None,
    opts: Sequence[Callable[[Options], None]] = (),
) -> Captcha:
    """Rotate captcha with custom background images; falls back to the
    bundled assets when unspecified."""
    from .. import resources as assets

    return (
        Builder(*opts)
        .set_resources(with_images(list(images) if images is not None else list(assets.get_images())))
        .make()
    )
