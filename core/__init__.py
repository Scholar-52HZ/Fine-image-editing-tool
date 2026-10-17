"""
Matting Studio - Core Package
提供本地化、高精度的图片抠图推理引擎、图像后处理管线与背景替换功能。
"""

from core.engine.base import MattingResult, BaseMattingEngine
from core.engine.matting_engine import AutoMattingEngine

__all__ = ["MattingResult", "BaseMattingEngine", "AutoMattingEngine"]
