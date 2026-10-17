"""
Base interfaces and result wrappers for matting engines.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Tuple, Optional
import numpy as np
from PIL import Image

from core.pipeline.composite import composite_with_color, composite_with_image


@dataclass
class MattingResult:
    """
    抠图结果封装类
    包含原始图、RGBA 透明前景图、灰度 Alpha 蒙版，并提供快速背景替换方法。
    """
    foreground: Image.Image  # RGBA 模式
    mask: Image.Image        # L 模式 (0-255)
    original: Image.Image    # 原始图像 (RGB)
    device_used: str = "cpu"
    fallback_notice: str = ""

    @property
    def size(self) -> Tuple[int, int]:
        """返回图像尺寸 (width, height)"""
        return self.foreground.size

    def to_mask_array(self) -> np.ndarray:
        """获取 Alpha 遮罩的 Numpy 数组 (0~255)"""
        return np.array(self.mask, dtype=np.uint8)

    def composite_color(self, color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]) -> Image.Image:
        """
        合成纯色背景（支持证件照换底色、电商白底等）
        :param color: 颜色 Hex 字符串（如 "#FFFFFF", "#1E90FF"）或 RGB/RGBA 元组
        :return: 合成后的 PIL Image (RGB 或 RGBA)
        """
        return composite_with_color(self.foreground, color)

    def composite_image(self, bg_image: Union[Image.Image, str, Path], mode: str = "cover") -> Image.Image:
        """
        合成自定义背景图片
        :param bg_image: 背景图 PIL 对象或文件路径
        :param mode: 缩放适配模式 ("cover", "contain", "stretch")
        :return: 合成后的 PIL Image (RGB)
        """
        if isinstance(bg_image, (str, Path)):
            bg_image = Image.open(bg_image)
        return composite_with_image(self.foreground, bg_image, mode=mode)

    def save(self, output_path: Union[str, Path], format: Optional[str] = None) -> Path:
        """
        保存透明前景图到磁盘
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # 默认保存为 PNG 以保留透明通道
        fmt = format or ("PNG" if path.suffix.lower() == ".png" else None)
        self.foreground.save(path, format=fmt)
        return path

    def save_mask(self, output_path: Union[str, Path]) -> Path:
        """保存单通道灰度 Alpha 遮罩图"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.mask.save(path, format="PNG")
        return path


class BaseMattingEngine(ABC):
    """
    抠图推理引擎抽象基类
    解耦具体推理实现（ONNX Runtime / Torch / Rembg / 外部模型权重）。
    """

    @abstractmethod
    def predict(
        self,
        image: Union[Image.Image, np.ndarray, str, Path, bytes],
        **kwargs
    ) -> MattingResult:
        """
        对输入图像执行抠图推理
        :param image: PIL 图像、Numpy 数组、本地路径或字节流
        :param kwargs: 引擎特有参数（如 alpha_matting 开关、阈值等）
        :return: MattingResult 结果对象
        """
        pass

    @classmethod
    @abstractmethod
    def supported_models(cls) -> list[str]:
        """返回引擎所支持的模型代号列表"""
        pass

    @property
    @abstractmethod
    def current_model(self) -> str:
        """返回当前加载的模型名称"""
        pass
