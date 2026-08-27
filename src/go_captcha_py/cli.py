"""CLI entry: generate sample captchas to files.

Usage:
    uv run go-captcha-py [outdir]
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import click, rotate, slide


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    outdir = Path(args[0]) if args else Path("captcha-output")
    outdir.mkdir(parents=True, exist_ok=True)

    text = click.make_default_text_captcha().generate()
    text.get_master_image().save_to_file(outdir / "click-text-master.jpg")
    text.get_thumb_image().save_to_file(outdir / "click-text-thumb.png")

    shape = click.make_default_shape_captcha().generate()
    shape.get_master_image().save_to_file(outdir / "click-shape-master.jpg")
    shape.get_thumb_image().save_to_file(outdir / "click-shape-thumb.png")

    s = slide.make_default_captcha().generate()
    s.get_master_image().save_to_file(outdir / "slide-master.jpg")
    s.get_tile_image().save_to_file(outdir / "slide-tile.png")

    d = slide.make_default_drag_drop_captcha().generate()
    d.get_master_image().save_to_file(outdir / "drag-master.jpg")
    d.get_tile_image().save_to_file(outdir / "drag-tile.png")

    r = rotate.make_default_captcha().generate()
    r.get_master_image().save_to_file(outdir / "rotate-master.png")
    r.get_thumb_image().save_to_file(outdir / "rotate-thumb.png")

    print(f"generated 9 sample images in {outdir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
