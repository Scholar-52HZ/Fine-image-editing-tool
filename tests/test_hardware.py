"""
Unit & Integration tests for hardware detection and device switching (CPU vs GPU DirectML).
"""

import pytest
from PIL import Image

from core.utils.hardware import (
    detect_hardware,
    get_device_choices,
    get_execution_providers,
    format_hardware_badge,
    HardwareInfo,
)
from core.engine.matting_engine import AutoMattingEngine
from ui.web.service import WebMattingService


def test_detect_hardware():
    info = detect_hardware(force_refresh=True)
    assert isinstance(info, HardwareInfo)
    assert info.cpu_name != ""
    assert info.cpu_cores >= 1
    assert "CPUExecutionProvider" in info.providers
    # 验证 DirectML 是否已成功识别
    assert info.has_directml is True
    assert "DmlExecutionProvider" in info.providers


def test_device_choices_default_cpu():
    choices = get_device_choices()
    assert len(choices) >= 1
    # 严格检验首项必须为 CPU 默认模式
    first_key, first_label = choices[0]
    assert first_key == "cpu"
    assert "默认" in first_label

    # 如果有 GPU，第二项应为 GPU
    if len(choices) > 1:
        assert choices[1][0] == "gpu"
        assert "GPU" in choices[1][1]


def test_get_execution_providers():
    # 测试 CPU 请求
    cpu_providers = get_execution_providers("cpu")
    assert cpu_providers == ["CPUExecutionProvider"]

    # 测试 GPU 请求 (当 DirectML 可用时应包含 DmlExecutionProvider)
    gpu_providers = get_execution_providers("gpu")
    assert "DmlExecutionProvider" in gpu_providers
    assert "CPUExecutionProvider" in gpu_providers


def test_format_hardware_badge():
    badge_cpu = format_hardware_badge("cpu")
    assert "CPU" in badge_cpu
    assert "默认" in badge_cpu

    badge_gpu = format_hardware_badge("gpu")
    assert "GPU" in badge_gpu


def test_engine_device_switching():
    engine = AutoMattingEngine(model_name="u2netp", device="cpu")
    assert engine.current_device == "cpu"

    engine.switch_device("gpu")
    assert engine.current_device == "gpu"

    engine.switch_device("cpu")
    assert engine.current_device == "cpu"


def test_webui_service_with_device():
    service = WebMattingService()
    sample_path = WebMattingService.create_sample_image()
    sample_img = Image.open(sample_path)

    # 1. 运行 CPU 推理 (默认)
    _, final_cpu, _, metrics_cpu = service.process_single(
        image=sample_img,
        model_name="u2netp",
        device="cpu",
        bg_mode="透明背景 (PNG)",
        preset_color_name="纯白 (#FFFFFF)",
        custom_color="#FFFFFF",
        custom_bg_image=None,
        bg_fit_mode="cover",
        feather_radius=0.0,
        alpha_matting=False,
        denoise=False,
        defringe=False,
    )
    assert final_cpu is not None
    assert "CPU" in metrics_cpu

    # 2. 运行 GPU 推理
    _, final_gpu, _, metrics_gpu = service.process_single(
        image=sample_img,
        model_name="u2netp",
        device="gpu",
        bg_mode="透明背景 (PNG)",
        preset_color_name="纯白 (#FFFFFF)",
        custom_color="#FFFFFF",
        custom_bg_image=None,
        bg_fit_mode="cover",
        feather_radius=0.0,
        alpha_matting=False,
        denoise=False,
        defringe=False,
    )
    assert final_gpu is not None
    assert "GPU" in metrics_gpu
