"""
Unit tests for core/engine (AutoMattingEngine and MattingResult).
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

from core.engine.base import MattingResult
from core.engine.matting_engine import AutoMattingEngine


def test_supported_models():
    models = AutoMattingEngine.supported_models()
    assert "bria-rmbg" in models
    assert "birefnet-general" in models
    assert "birefnet-portrait" in models
    assert "u2net" in models
    assert "u2netp" in models


def test_engine_initialization_and_switching():
    engine = AutoMattingEngine(model_name="bria-rmbg")
    assert engine.current_model == "bria-rmbg"

    engine.switch_model("u2netp")
    assert engine.current_model == "u2netp"

    with pytest.raises(ValueError, match="不支持的模型代号"):
        AutoMattingEngine(model_name="non_existent_model")

    with pytest.raises(ValueError, match="不支持的模型代号"):
        engine.switch_model("invalid_model")


def test_matting_result_save_and_composite(tmp_path):
    fg = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    mask = Image.new("L", (64, 64), 255)
    orig = Image.new("RGB", (64, 64), (255, 0, 0))

    result = MattingResult(foreground=fg, mask=mask, original=orig)

    assert result.size == (64, 64)
    mask_arr = result.to_mask_array()
    assert mask_arr.shape == (64, 64)
    assert mask_arr.dtype == np.uint8

    # 保存测试
    fg_file = tmp_path / "fg.png"
    mask_file = tmp_path / "mask.png"
    result.save(fg_file)
    result.save_mask(mask_file)

    assert fg_file.exists()
    assert mask_file.exists()

    # 纯色合成测试
    comp_white = result.composite_color("#FFFFFF")
    assert comp_white.mode == "RGB"
    assert comp_white.size == (64, 64)


def test_predict_pipeline_with_mock():
    engine = AutoMattingEngine(model_name="bria-rmbg")

    # 创建假的前景返回 (RGBA)
    mock_fg = Image.new("RGBA", (50, 50), (100, 150, 200, 255))
    # 在四周设置半透明以测试后处理逻辑
    mock_arr = np.array(mock_fg)
    mock_arr[0:5, :, 3] = 128
    mock_fg = Image.fromarray(mock_arr, mode="RGBA")

    with patch("rembg.new_session", return_value=MagicMock()) as mock_session:
        with patch("rembg.remove", return_value=mock_fg) as mock_remove:
            # 1. 传入 PIL Image
            test_img = Image.new("RGB", (50, 50), (255, 255, 255))
            res = engine.predict(
                test_img,
                alpha_matting=False,
                feather_radius=1.0,
                denoise=True,
                defringe=False,
            )

            assert isinstance(res, MattingResult)
            assert res.foreground.mode == "RGBA"
            assert res.mask.mode == "L"
            assert res.size == (50, 50)
            mock_remove.assert_called_once()

            # 2. 传入 Numpy Array
            mock_remove.reset_mock()
            np_img = np.zeros((50, 50, 3), dtype=np.uint8)
            res_np = engine.predict(np_img)
            assert isinstance(res_np, MattingResult)
            mock_remove.assert_called_once()
