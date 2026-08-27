"""Slide captcha drawing engine, ported from go-captcha/v2/slide/draw.go."""

from __future__ import annotations

from PIL import Image

from ..base.helper import create_nrgba_canvas
from .block import Block


class DrawBlock:
    """Drawing instruction for one notch block."""

    __slots__ = ("angle", "block", "height", "image", "width", "x", "y")

    def __init__(
        self,
        block: Block,
        x: int,
        y: int,
        image: Image.Image,
        width: int,
        height: int,
        angle: int,
    ) -> None:
        self.block = block
        self.x = x
        self.y = y
        self.image = image
        self.width = width
        self.height = height
        self.angle = angle


class DrawImageParams:
    """Master image drawing params (DrawImageParams in slide/draw.go)."""

    __slots__ = ("alpha", "background", "captcha_draw_blocks", "height", "width")

    def __init__(
        self,
        width: int,
        height: int,
        background: Image.Image | None,
        alpha: float,
        captcha_draw_blocks: list[DrawBlock],
    ) -> None:
        self.width = width
        self.height = height
        self.background = background
        self.alpha = alpha
        self.captcha_draw_blocks = captcha_draw_blocks


class DrawTplImageParams:
    """Tile image drawing params (DrawTplImageParams in slide/draw.go)."""

    __slots__ = ("alpha", "background", "captcha_draw_block", "height", "mask_image", "width")

    def __init__(
        self,
        background: Image.Image,
        mask_image: Image.Image,
        alpha: float,
        width: int,
        height: int,
        captcha_draw_block: DrawBlock,
    ) -> None:
        self.background = background
        self.mask_image = mask_image
        self.alpha = alpha
        self.width = width
        self.height = height
        self.captcha_draw_block = captcha_draw_block


class DrawImage:
    """Concrete slide drawing implementation (drawImage in slide/draw.go)."""

    def draw_with_nrgba(self, params: DrawImageParams) -> tuple[Image.Image, Image.Image]:
        """Draw the master image (notch shadow burnt in) + clean background.

        Returns (master_image, master_bg_image). Mirrors DrawWithNRGBA.
        """
        blocks = params.captcha_draw_blocks
        cvs = create_nrgba_canvas(params.width, params.height, True)

        for block in blocks:
            graph = self._draw_graph_image(block.width, block.height, block.image)
            cvs.alpha_composite(graph, dest=(block.x, block.y))

        rcm = create_nrgba_canvas(params.width, params.height, True)
        if params.background is not None:
            bg = params.background.convert("RGB")
            m = create_nrgba_canvas(params.width, params.height, True)
            m.paste(bg, (0, 0), None)
            rcm.alpha_composite(m, dest=(0, 0))
            m.alpha_composite(cvs, dest=(0, 0))
            return m, rcm
        return cvs, rcm

    def draw_with_template(self, params: DrawTplImageParams) -> Image.Image:
        """Draw the draggable tile: background cut through the mask + overlay.

        Mirrors DrawWithTemplate.
        """
        block = params.captcha_draw_block
        cvs = create_nrgba_canvas(params.width, params.height, True)
        bg_cvs = create_nrgba_canvas(params.width, params.height, True)

        tpl_mask = self._draw_graph_image(params.width, params.height, params.mask_image)

        # copy the block-sized region of the master background at (block.x, block.y)
        bg_img = params.background.convert("RGB")
        region = bg_img.crop((block.x, block.y, block.x + params.width, block.y + params.height))
        bg_cvs.paste(region, (0, 0))

        # cut the region with the mask shape
        mask_alpha = tpl_mask.split()[3]
        cut = Image.composite(bg_cvs, create_nrgba_canvas(params.width, params.height, True), mask_alpha)
        cvs.alpha_composite(cut, dest=(0, 0))

        # add the overlay border graphics on top
        overlay = self._draw_graph_image(params.width, params.height, block.image)
        cvs.alpha_composite(overlay, dest=(0, 0))
        return cvs

    @staticmethod
    def _draw_graph_image(width: int, height: int, img: Image.Image) -> Image.Image:
        """Bilinear-scale a graph image to width x height. Mirrors drawGraphImage."""
        src = img if img.mode == "RGBA" else img.convert("RGBA")
        if src.size != (width, height):
            src = src.resize((width, height), Image.BICUBIC)
        return src
