"""
Automated unit & integration tests for ui/web (WebMattingService and Gradio Blocks).
"""

import zipfile
from pathlib import Path
from PIL import Image
import pytest

from ui.web.service import WebMattingService, ID_PHOTO_SPECS, ID_PHOTO_COLORS
from ui.web.app import create_app, toggle_bg_controls


@pytest.fixture
def service():
    return WebMattingService()


@pytest.fixture
def sample_image():
    # 生成测试用图像 (红球带绿色背景)
    img_path = WebMattingService.create_sample_image()
    return Image.open(img_path)


def test_create_sample_image():
    path = WebMattingService.create_sample_image()
    assert Path(path).exists()
    img = Image.open(path)
    assert img.size == (400, 400)


def test_toggle_bg_controls():
    # 测试预设纯色模式
    u1, u2, u3, u4 = toggle_bg_controls("预设纯色背景")
    assert u1["visible"] is True
    assert u2["visible"] is False
    assert u3["visible"] is False

    # 测试自定义颜色模式
    u1, u2, u3, u4 = toggle_bg_controls("自定义颜色")
    assert u1["visible"] is False
    assert u2["visible"] is True
    assert u3["visible"] is False

    # 测试自定义背景图模式
    u1, u2, u3, u4 = toggle_bg_controls("自定义背景图")
    assert u1["visible"] is False
    assert u2["visible"] is False
    assert u3["visible"] is True
    assert u4["visible"] is True


def test_process_single_transparent(service, sample_image):
    # 使用轻量级 u2netp 测试单图透明抠图
    slider_pair, final_img, mask_img, metrics = service.process_single(
        image=sample_image,
        model_name="u2netp",
        bg_mode="透明背景 (PNG)",
        preset_color_name="纯白 (#FFFFFF)",
        custom_color="#FFFFFF",
        custom_bg_image=None,
        bg_fit_mode="cover",
        feather_radius=0.5,
        alpha_matting=False,
        denoise=True,
        defringe=False,
    )

    assert slider_pair is not None
    assert final_img is not None
    assert mask_img is not None
    assert final_img.mode == "RGBA"
    assert mask_img.mode == "L"
    assert "u2netp" in metrics
    assert "处理完成指标" in metrics


def test_process_single_solid_color(service, sample_image):
    # 测试预设纯白底色
    _, final_white, _, _ = service.process_single(
        image=sample_image,
        model_name="u2netp",
        bg_mode="预设纯色背景",
        preset_color_name="纯白 (#FFFFFF)",
        custom_color="#FFFFFF",
        custom_bg_image=None,
        bg_fit_mode="cover",
        feather_radius=0.0,
        alpha_matting=False,
        denoise=False,
        defringe=False,
    )
    assert final_white.mode == "RGB"
    # 背景角落像素应为白色
    assert final_white.getpixel((5, 5)) == (255, 255, 255)

    # 测试自定义颜色 (例如纯红 #FF0000)
    _, final_red, _, _ = service.process_single(
        image=sample_image,
        model_name="u2netp",
        bg_mode="自定义颜色",
        preset_color_name="",
        custom_color="#FF0000",
        custom_bg_image=None,
        bg_fit_mode="cover",
        feather_radius=0.0,
        alpha_matting=False,
        denoise=False,
        defringe=False,
    )
    assert final_red.mode == "RGB"
    assert final_red.getpixel((5, 5)) == (255, 0, 0)


def test_process_single_none_input(service):
    slider_pair, final_img, mask_img, metrics = service.process_single(
        image=None,
        model_name="u2netp",
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
    assert slider_pair is None
    assert final_img is None
    assert "请先上传" in metrics


def test_process_id_photo(service, sample_image):
    # 测试标准一寸证件照生成
    id_img, cutout_img, info = service.process_id_photo(
        image=sample_image,
        spec_name="一寸 (295 × 413 px, 25 × 35 mm)",
        color_name="标准蓝底 (#438EDB)",
        model_name="u2netp",
        feather_radius=0.5,
        denoise=True,
    )

    assert id_img is not None
    assert cutout_img is not None
    assert id_img.size == (295, 413)
    assert id_img.mode == "RGB"
    # 角落应为标准蓝底 (#438EDB -> 67, 142, 219)
    corner_pixel = id_img.getpixel((5, 5))
    assert corner_pixel == (67, 142, 219)
    assert "一寸" in info

    # 测试二寸规格 (413 × 579)
    id_img_2, _, _ = service.process_id_photo(
        image=sample_image,
        spec_name="二寸 (413 × 579 px, 35 × 49 mm)",
        color_name="标准白底 (#FFFFFF)",
        model_name="u2netp",
        feather_radius=0.0,
        denoise=False,
    )
    assert id_img_2.size == (413, 579)


def test_process_batch(service, tmp_path):
    # 创建2个临时图片文件
    img1_path = tmp_path / "img1.png"
    img2_path = tmp_path / "img2.png"

    sample = Image.new("RGB", (64, 64), (100, 200, 50))
    sample.save(img1_path)
    sample.save(img2_path)

    # 包装为模拟文件对象
    class FakeFile:
        def __init__(self, p):
            self.name = str(p)

    files = [FakeFile(img1_path), FakeFile(img2_path)]

    zip_path, table_data, summary = service.process_batch(
        files=files,
        model_name="u2netp",
        bg_mode="预设纯色背景",
        preset_color_name="纯白 (#FFFFFF)",
        custom_color="",
        feather_radius=0.0,
        denoise=False,
    )

    assert zip_path is not None
    assert Path(zip_path).exists()
    assert len(table_data) == 2
    assert "成功" in summary

    # 验证 zip 包内文件
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        assert any("img1" in name for name in namelist)
        assert any("img2" in name for name in namelist)


def test_gradio_app_structure():
    # 测试 Gradio Blocks 构建无语法或组件配置错误
    import gradio as gr
    app = create_app()
    assert app is not None
    assert hasattr(app, "render")

    # 严格检验所有 Radio 组件的默认 value 均在 choices 之中
    radios = [c for c in app.blocks.values() if isinstance(c, gr.Radio)]
    for r in radios:
        valid_values = [choice[1] if isinstance(choice, (list, tuple)) else choice for choice in r.choices]
        assert r.value in valid_values, f"Radio {r.label} default value '{r.value}' not in {valid_values}"

