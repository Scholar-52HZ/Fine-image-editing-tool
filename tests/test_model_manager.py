"""
Unit tests for model asset management and resolution system (core/utils/model_manager.py).
"""

from pathlib import Path
import pytest

from core.utils.model_manager import (
    find_model_path,
    is_model_ready,
    get_model_status,
    get_all_models_status,
    format_model_choice_label,
    SUPPORTED_MODELS_META,
    LOCAL_MODELS_DIR,
)
from ui.web.service import WebMattingService


def test_supported_models_meta():
    assert len(SUPPORTED_MODELS_META) >= 5
    assert "u2netp" in SUPPORTED_MODELS_META
    assert "bria-rmbg" in SUPPORTED_MODELS_META

    u2 = SUPPORTED_MODELS_META["u2netp"]
    assert u2.is_builtin is True
    assert u2.filename == "u2netp.onnx"
    assert "Scholar-52HZ" in u2.direct_user_release_url
    assert len(u2.get_download_urls(use_mirror=True)) > 2


def test_find_model_path_builtin():
    # 验证内置的 u2netp.onnx 是否被成功解析定位
    path = find_model_path("u2netp")
    assert path is not None
    assert path.exists()
    assert "u2netp.onnx" in str(path)
    assert is_model_ready("u2netp") is True


def test_get_model_status():
    status = get_model_status("u2netp")
    assert status["name"] == "u2netp"
    assert status["is_ready"] is True
    assert status["is_builtin"] is True
    assert "✅" in status["badge"]

    # 测试未就绪模型的状态格式
    unready = get_model_status("u2net")
    if not unready["is_ready"]:
        assert "⬇️" in unready["badge"]
        assert unready["local_path"] == "未就绪"


def test_format_model_choice_label():
    label = format_model_choice_label("u2netp")
    assert "u2netp" in label
    assert "已就绪" in label


def test_web_service_model_methods():
    service = WebMattingService()
    choices = service.get_model_choices()
    assert len(choices) >= 5
    # 首项应为 u2netp
    first_label, first_name = choices[0]
    assert first_name == "u2netp"
    assert "u2netp" in first_label

    table_data = service.get_model_status_table()
    assert len(table_data) == len(SUPPORTED_MODELS_META)
    assert len(table_data[0]) == 6  # 6 列
