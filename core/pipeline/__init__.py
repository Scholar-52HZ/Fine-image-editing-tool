"""
Pipeline module for image refinement, background compositing and post-processing.
"""

from core.pipeline.composite import (
    parse_color,
    composite_with_color,
    composite_with_image,
)
from core.pipeline.refine import (
    feather_mask,
    remove_small_noise,
    defringe_foreground,
)

__all__ = [
    "parse_color",
    "composite_with_color",
    "composite_with_image",
    "feather_mask",
    "remove_small_noise",
    "defringe_foreground",
]
