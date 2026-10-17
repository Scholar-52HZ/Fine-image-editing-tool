"""
AutoMattingEngine - 基于 ONNX Runtime 与前沿深度学习架构的高精度抠图推理引擎。
统一支持 RMBG、BiRefNet、U-2-Net、IS-Net 等 SOTA 离线模型。
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import numpy as np
from PIL import Image

import rembg
from core.engine.base import BaseMattingEngine, MattingResult
from core.pipeline.refine import feather_mask, remove_small_noise, defringe_foreground
from core.utils.hardware import get_execution_providers, detect_hardware
from core.utils.model_manager import (
    find_model_path,
    is_model_ready,
    get_model_status,
    patch_rembg_resolver,
    SUPPORTED_MODELS_META,
)

# 确保 rembg 会话基类加载项目本地 models/ 优先解析
patch_rembg_resolver()


class AutoMattingEngine(BaseMattingEngine):
    """
    自动抠图引擎
    集成 ONNX Runtime 会话缓存，支持多种前沿模型动态切换与 CPU/GPU (DirectML) 自主配置调度。
    """

    MODEL_REGISTRY: Dict[str, str] = {
        "u2netp": "U-2-Net Portable 轻量快速模型 (推荐 · CPU/GPU 极速秒级)",
        "bria-rmbg": "Bria RMBG 2.0 高保真发丝级模型 (1GB 体积 · 建议 CPU 软解)",
        "birefnet-portrait": "BiRefNet 专为人像发丝优化的精细模型",
        "birefnet-general": "BiRefNet 高分辨率双边参考通用模型",
        "u2net": "U-2-Net 经典高精度通用显著性分割模型",
        "silueta": "Silueta 超轻量级快速模型 (~43MB)",
        "isnet-general-use": "IS-Net 高精度目标物体分割",
    }

    def __init__(
        self,
        model_name: str = "u2netp",
        device: str = "cpu",
        providers: Optional[List[str]] = None,
        models_dir: Optional[Union[str, Path]] = None,
    ):
        """
        :param model_name: 模型代号，可选: bria-rmbg, birefnet-general, birefnet-portrait, u2net, u2netp 等
        :param device: 计算设备，"cpu" (默认) 或 "gpu" (DirectML / CUDA)
        :param providers: 显式指定 ONNX Runtime 执行提供者 (默认根据 device 自动映射)
        :param models_dir: 本地模型权重缓存路径，默认 ~/.u2net
        """
        if model_name not in self.MODEL_REGISTRY:
            supported = ", ".join(self.MODEL_REGISTRY.keys())
            raise ValueError(f"不支持的模型代号 '{model_name}'。支持列表: {supported}")

        self._current_model: str = model_name
        self._current_device: str = device.lower().strip()
        self._providers = providers or get_execution_providers(self._current_device)
        self._models_dir = str(models_dir) if models_dir else None
        # 会话缓存键为 (model_name, device) 元组，彻底隔离 CPU 与 GPU 会话
        self._sessions: Dict[Tuple[str, str], Any] = {}

    @classmethod
    def supported_models(cls) -> List[str]:
        """返回引擎所支持的模型代号列表"""
        return list(cls.MODEL_REGISTRY.keys())

    @classmethod
    def get_model_descriptions(cls) -> Dict[str, str]:
        """获取所有支持模型的详细描述"""
        return cls.MODEL_REGISTRY.copy()

    @property
    def current_model(self) -> str:
        """返回当前加载的模型名称"""
        return self._current_model

    @property
    def current_device(self) -> str:
        """返回当前设置的计算设备"""
        return self._current_device

    def switch_model(self, model_name: str) -> None:
        """动态切换当前推理使用的模型"""
        if model_name not in self.MODEL_REGISTRY:
            supported = ", ".join(self.MODEL_REGISTRY.keys())
            raise ValueError(f"不支持的模型代号 '{model_name}'。支持列表: {supported}")
        self._current_model = model_name

    def switch_device(self, device: str) -> None:
        """动态切换当前推理计算设备 (cpu / gpu)"""
        self._current_device = device.lower().strip()
        self._providers = get_execution_providers(self._current_device)

    def _get_or_create_session(self, model_name: str, device: Optional[str] = None):
        """获取或创建 ONNX Runtime 会话（按 (model_name, device) 隔离缓存）"""
        target_device = (device or self._current_device).lower().strip()
        cache_key = (model_name, target_device)

        if cache_key not in self._sessions:
            providers = get_execution_providers(target_device)
            kwargs = {"providers": providers}
            # rembg.new_session 自动从官方安全镜像拉取并缓存至本地
            session = rembg.new_session(model_name, **kwargs)
            self._sessions[cache_key] = session
        return self._sessions[cache_key]

    def _load_image(self, image: Union[Image.Image, np.ndarray, str, Path, bytes]) -> Image.Image:
        """将各种输入格式统一解析为 RGB PIL.Image"""
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        elif isinstance(image, np.ndarray):
            if image.ndim == 2:
                img = Image.fromarray(image, mode="L").convert("RGB")
            elif image.shape[2] == 4:
                img = Image.fromarray(image, mode="RGBA").convert("RGB")
            else:
                img = Image.fromarray(image, mode="RGB")
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise TypeError(f"不支持的输入图像类型: {type(image)}")

        # 确保转为 RGB，并标准化 EXIF 方向
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img

    def predict(
        self,
        image: Union[Image.Image, np.ndarray, str, Path, bytes],
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10,
        feather_radius: float = 0.0,
        denoise: bool = False,
        defringe: bool = False,
        **kwargs
    ) -> MattingResult:
        """
        对输入图像执行抠图推理与 Alpha 通道生成
        :param image: 输入图像 (PIL Image / Path / ndarray / bytes)
        :param model_name: 临时覆盖当前模型（可选）
        :param device: 临时覆盖当前计算设备 ("cpu" / "gpu")
        :param alpha_matting: 是否开启基于三值图的 Alpha Matting 精细羽化 (针对极细发丝)
        :param alpha_matting_foreground_threshold: 确定前景阈值 (0-255)
        :param alpha_matting_background_threshold: 确定背景阈值 (0-255)
        :param alpha_matting_erode_size: 侵蚀腐蚀核大小
        :param feather_radius: 边缘高斯平滑半径 (0 表示不羽化)
        :param denoise: 是否执行杂点消除与微小空洞修补
        :param defringe: 是否执行边缘色溢与背景反光净化
        :return: MattingResult (含透明前景图、灰度遮罩与原图)
        """
        orig_img = self._load_image(image)
        target_model = model_name or self._current_model
        target_device = (device or self._current_device).lower().strip()

        # 安全防截断校验：如果用户选择了尚未离线就绪的模型，禁止静默网络卡顿，主动提供明确指引
        if not is_model_ready(target_model):
            status = get_model_status(target_model)
            raise FileNotFoundError(
                f"模型 [{target_model}] 在本地尚未就绪 ({status['size_str']})。"
                f"建议先选用已内置就绪的 u2netp，或前往【📦 离线模型管理】页面高速预下载。"
            )

        actual_device = target_device
        fallback_notice = ""

        # 执行推理，若在 GPU 模式发生 DirectML 兼容性异常或显存溢出，自动安全回退至 CPU 软解
        try:
            session = self._get_or_create_session(target_model, target_device)
            fg_rgba = rembg.remove(
                orig_img,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size,
                **kwargs
            )
        except Exception as exc:
            if target_device in ("gpu", "dml", "cuda"):
                # GPU 模式失败，安全无缝降级为 CPU 模式重试
                actual_device = "cpu"
                fallback_notice = "（⚠️ 硬件提示：当前模型在独显运行受限或显存不足，已自动安全回退至 CPU 软解完成）"
                cpu_session = self._get_or_create_session(target_model, "cpu")
                fg_rgba = rembg.remove(
                    orig_img,
                    session=cpu_session,
                    alpha_matting=alpha_matting,
                    alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                    alpha_matting_background_threshold=alpha_matting_background_threshold,
                    alpha_matting_erode_size=alpha_matting_erode_size,
                    **kwargs
                )
            else:
                raise exc

        if fg_rgba.mode != "RGBA":
            fg_rgba = fg_rgba.convert("RGBA")

        # 提取 Alpha 单通道遮罩
        mask = fg_rgba.split()[-1]

        # 图像后处理：去杂点与空洞
        if denoise:
            mask = remove_small_noise(mask)

        # 图像后处理：边缘羽化
        if feather_radius > 0:
            mask = feather_mask(mask, radius=feather_radius)

        # 将可能更新后的 mask 重新写回 RGBA
        fg_rgba.putalpha(mask)

        # 图像后处理：边缘色溢净化
        if defringe:
            fg_rgba = defringe_foreground(fg_rgba, mask)

        return MattingResult(
            foreground=fg_rgba,
            mask=mask,
            original=orig_img,
            device_used=actual_device,
            fallback_notice=fallback_notice,
        )

