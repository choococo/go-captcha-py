"""go-captcha-py: Python implementation of GoCaptcha behavior captcha.

Port of https://github.com/wenlng/go-captcha (Go) to Python, with bundled
image/shape/tile/font assets. Supports click / slide / drag-drop / rotate
captcha generation and validation, wire-compatible with the official
go-captcha frontends (Vue / React / Angular / Svelte / Solid / JS).

Quick start:
    from go_captcha_py import click

    capt = click.make_default_text_captcha()
    data = capt.generate()
    answer = data.get_data()                    # keep server-side
    image = data.get_master_image().to_base64() # send to the client
"""

from . import base, click, resources, rotate, slide, store

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "base",
    "click",
    "resources",
    "rotate",
    "slide",
    "store",
]
