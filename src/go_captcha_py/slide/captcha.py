"""Slide captcha generator, ported from go-captcha/v2/slide/slide.go."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from ..base.imagedata import JPEGImageData, PNGImageData
from ..base.option import Point, RangeVal, Size
from ..base.randgen import rand_image, rand_index, rand_int_fast
from .block import Block
from .draw import DrawBlock, DrawImage, DrawImageParams, DrawTplImageParams
from .options import (
    DEAD_ZONE_DIRECTION_BOTTOM,
    DEAD_ZONE_DIRECTION_LEFT,
    DEAD_ZONE_DIRECTION_RIGHT,
    DEAD_ZONE_DIRECTION_TOP,
    Options,
    Resources,
)

MODE_BASIC = 0
MODE_DRAG = 1


class CaptchaError(Exception):
    """Slide captcha generation error."""


GRAPH_IMAGE_ERR = "graph image is invalid"
GENERATE_DATA_ERR = "data generation failed"
IMAGE_TYPE_ERR = "tile image must be of type image.Image"
SHADOW_IMAGE_TYPE_ERR = "tile shadow image must be of type image.Image"
MASK_IMAGE_TYPE_ERR = "tile mask image must be of type image.Image"
EMPTY_BACKGROUND_IMAGE_ERR = "no background image"


@dataclass(slots=True)
class CaptchaData:
    """Generated slide captcha: block + master image + tile image."""

    block: Block
    master_image: JPEGImageData
    tile_image: PNGImageData

    def get_data(self) -> Block:
        """Verification block (kept server-side)."""
        return self.block

    def get_master_image(self) -> JPEGImageData:
        """Main captcha image with the burnt-in notch shadow."""
        return self.master_image

    def get_tile_image(self) -> PNGImageData:
        """The draggable puzzle tile."""
        return self.tile_image


class Captcha:
    """Slide captcha implementation (captcha struct in slide.go)."""

    def __init__(
        self,
        mode: int = MODE_BASIC,
        opts: Options | None = None,
        resources: Resources | None = None,
    ) -> None:
        self.mode = mode
        self.opts = opts if opts is not None else Options()
        self.resources = resources if resources is not None else Resources()
        self._draw = DrawImage()

        if mode == MODE_BASIC:
            # basic mode: single left dead-zone, fixed Y (newWithMode)
            self.opts.range_dead_zone_directions = [DEAD_ZONE_DIRECTION_LEFT]
            self.opts.enable_graph_vertical_random = False
        elif mode == MODE_DRAG:
            # drag-drop mode uses two candidate holes: one real target and
            # one distractor. The draggable tile is cut from the selected
            # target, so its background texture reveals the correct hole.
            self.opts.gen_graph_number = 2
            self.opts.enable_graph_vertical_random = True

    # ------------------------------------------------------------------

    def generate(self) -> CaptchaData:
        """Generate a slide captcha. Raises CaptchaError on invalid config."""
        self._check()

        overlay_image, shadow_image, mask_image = self._gen_graph()
        if overlay_image is None or shadow_image is None or mask_image is None:
            raise CaptchaError(GRAPH_IMAGE_ERR)

        blocks, tile_point = self._gen_graph_blocks(
            self.opts.image_size, self.opts.range_graph_size, self.opts.gen_graph_number
        )
        if len(blocks) > 1:
            index = max(rand_index(len(blocks)), 0)
            block = blocks[index]
        else:
            block = blocks[0]

        if block is None:
            raise CaptchaError(GENERATE_DATA_ERR)

        master_image, master_bg_image = self._gen_master_image(self.opts.image_size, shadow_image, blocks)
        tile_image = self._gen_tile_image(mask_image, master_bg_image, overlay_image, block)

        if self.mode == MODE_BASIC:
            block.tile_y = block.y
            block.dy = block.y
        else:
            block.tile_y = tile_point.y
            block.dy = tile_point.y
        block.tile_x = tile_point.x
        block.dx = tile_point.x

        return CaptchaData(
            block=block,
            master_image=JPEGImageData(master_image),
            tile_image=PNGImageData(tile_image),
        )

    # ------------------------------------------------------------------

    def _gen_master_image(
        self, size: Size, shadow_image: Image.Image, blocks: list[Block]
    ) -> tuple[Image.Image, Image.Image]:
        draw_blocks = [
            DrawBlock(
                block=b,
                x=b.x,
                y=b.y,
                width=b.width,
                height=b.height,
                angle=b.angle,
                image=shadow_image,
            )
            for b in blocks
        ]
        return self._draw.draw_with_nrgba(
            DrawImageParams(
                width=size.width,
                height=size.height,
                background=rand_image(self.resources.backgrounds),
                alpha=self.opts.image_alpha,
                captcha_draw_blocks=draw_blocks,
            )
        )

    def _gen_tile_image(
        self,
        mask_image: Image.Image,
        bg_image: Image.Image,
        overlay_image: Image.Image,
        block: Block,
    ) -> Image.Image:
        return self._draw.draw_with_template(
            DrawTplImageParams(
                background=bg_image,
                mask_image=mask_image,
                alpha=self.opts.image_alpha,
                width=block.width,
                height=block.height,
                captcha_draw_block=DrawBlock(
                    block=block,
                    x=block.x,
                    y=block.y,
                    width=block.width,
                    height=block.height,
                    angle=block.angle,
                    image=overlay_image,
                ),
            )
        )

    # ------------------------------------------------------------------

    def _rand_dead_zone_direction(self) -> int:
        dirs = self.opts.range_dead_zone_directions
        index = rand_index(len(dirs))
        if index < 0:
            return 0
        return dirs[index]

    def _rand_graph_angle(self) -> int:
        angles = self.opts.range_graph_angle_pos
        index = rand_index(len(angles))
        if index < 0:
            return 0
        angle = angles[index]
        return rand_int_fast(angle.min, angle.max)

    def _gen_graph_blocks(self, image_size: Size, size: RangeVal, length: int) -> tuple[list[Block], Point]:
        """Generate notch blocks + tile start point. Mirrors genGraphBlocks."""
        blocks: list[Block] = []
        width = image_size.width
        height = image_size.height

        rand_angle = self._rand_graph_angle()
        rand_size = rand_int_fast(size.min, size.max)
        c_height = rand_size
        c_width = rand_size

        dzd_type = self._rand_dead_zone_direction()
        dp = c_width // 2
        block_width = (width - c_width - 20) // max(length, 1)
        y = self._calc_y_with_dead_zone(5, height - c_height - 5, c_height, dzd_type)

        for i in range(length):
            start, end = self._calc_x_with_dead_zone(
                (i * block_width) + dp + 5, ((i + 1) * block_width) - dp, c_width, dzd_type
            )
            start = int(max(start, dp + 5))
            x = rand_int_fast(start + 20, end + 20) - dp

            if self.opts.enable_graph_vertical_random:
                y = self._calc_y_with_dead_zone(5, height - c_height - 5, c_height, dzd_type)

            blocks.append(Block(x=x, y=y, width=c_width, height=c_height, angle=rand_angle))

        point = Point(0, 0)
        if self.mode == MODE_BASIC:
            point.x = rand_int_fast(5, max(dp, 6))
            point.y = y
            return blocks, point

        if dzd_type == DEAD_ZONE_DIRECTION_TOP:
            point.x = rand_int_fast(5, width - c_width - 5)
            point.y = 5
        elif dzd_type == DEAD_ZONE_DIRECTION_BOTTOM:
            point.x = rand_int_fast(5, width - c_width - 5)
            point.y = height - c_height - 5
        elif dzd_type == DEAD_ZONE_DIRECTION_LEFT:
            point.x = 5
            point.y = rand_int_fast(5, height - c_height - 5)
        elif dzd_type == DEAD_ZONE_DIRECTION_RIGHT:
            point.x = width - c_width - 5
            point.y = rand_int_fast(5, height - c_height - 5)

        return blocks, point

    @staticmethod
    def _calc_x_with_dead_zone(start: int, end: int, value: int, dzd_type: int) -> tuple[int, int]:
        if dzd_type == DEAD_ZONE_DIRECTION_LEFT:
            start += value
            end += value
        return start, end

    @staticmethod
    def _calc_y_with_dead_zone(start: int, end: int, value: int, dzd_type: int) -> int:
        if dzd_type == DEAD_ZONE_DIRECTION_TOP:
            start += value
        elif dzd_type == DEAD_ZONE_DIRECTION_BOTTOM:
            end -= value
        return rand_int_fast(start, end)

    def _gen_graph(self) -> tuple[Image.Image | None, Image.Image | None, Image.Image | None]:
        index = rand_index(len(self.resources.graph_images))
        if index < 0:
            return None, None, None
        graph = self.resources.graph_images[index]
        return graph.overlay_image, graph.shadow_image, graph.mask_image

    def _check(self) -> None:
        for tile in self.resources.graph_images:
            if tile.overlay_image is None:
                raise CaptchaError(IMAGE_TYPE_ERR)
            if tile.shadow_image is None:
                raise CaptchaError(SHADOW_IMAGE_TYPE_ERR)
            if tile.mask_image is None:
                raise CaptchaError(MASK_IMAGE_TYPE_ERR)
        if not self.resources.backgrounds:
            raise CaptchaError(EMPTY_BACKGROUND_IMAGE_ERR)
