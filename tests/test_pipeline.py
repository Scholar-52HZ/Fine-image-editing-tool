"""
Unit tests for core/pipeline (composite and refine).
"""

import numpy as np
import pytest
from PIL import Image

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


def test_parse_color():
    # 6-digit hex
    assert parse_color("#FFFFFF") == (255, 255, 255, 255)
    assert parse_color("#000000") == (0, 0, 0, 255)
    assert parse_color("1E90FF") == (30, 144, 255, 255)

    # 3-digit hex
    assert parse_color("#FFF") == (255, 255, 255, 255)

    # 8-digit hex
    assert parse_color("#FFFFFF80") == (255, 255, 255, 128)

    # Named colors
    assert parse_color("white") == (255, 255, 255, 255)
    assert parse_color("id_blue") == (67, 142, 219, 255)
    assert parse_color("transparent") == (0, 0, 0, 0)

    # Tuples
    assert parse_color((255, 0, 0)) == (255, 0, 0, 255)
    assert parse_color((0, 255, 0, 100)) == (0, 255, 0, 100)

    # Invalid
    with pytest.raises(ValueError):
        parse_color("invalid_color_xyz")


def test_composite_with_color():
    # 创建 100x100 RGBA 前景：左半边是不透明白色，右半边完全透明
    fg_arr = np.zeros((100, 100, 4), dtype=np.uint8)
    fg_arr[:, :50] = [255, 255, 255, 255]  # 左半边
    fg = Image.fromarray(fg_arr, mode="RGBA")

    # 与纯红色背景合成
    comp = composite_with_color(fg, "#FF0000")
    assert comp.mode == "RGB"
    assert comp.size == (100, 100)

    comp_arr = np.array(comp)
    # 左半边应当是前景白色 (255, 255, 255)
    assert np.all(comp_arr[:, 20] == [255, 255, 255])
    # 右半边应当是背景红色 (255, 0, 0)
    assert np.all(comp_arr[:, 80] == [255, 0, 0])


def test_composite_with_image():
    fg = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
    # 在中心画一个 50x50 的不透明方块
    fg_arr = np.array(fg)
    fg_arr[25:75, 25:75] = [255, 0, 0, 255]
    fg = Image.fromarray(fg_arr, mode="RGBA")

    bg = Image.new("RGB", (200, 150), (0, 255, 0))

    # 测试 cover 模式
    comp = composite_with_image(fg, bg, mode="cover")
    assert comp.mode == "RGB"
    assert comp.size == (100, 100)

    comp_arr = np.array(comp)
    # 中心区域应当是红色
    assert np.all(comp_arr[50, 50] == [255, 0, 0])
    # 四周应当是背景绿色
    assert np.all(comp_arr[10, 10] == [0, 255, 0])


def test_feather_mask():
    mask = Image.new("L", (50, 50), 0)
    # 在中间填充 20x20 的高亮区域
    mask_arr = np.array(mask)
    mask_arr[15:35, 15:35] = 255
    mask = Image.fromarray(mask_arr, mode="L")

    feathered = feather_mask(mask, radius=2.0)
    assert feathered.size == (50, 50)
    f_arr = np.array(feathered)
    # 边缘应当有渐变半透明过渡值 (0 < val < 255)
    transition_pixels = np.any((f_arr > 0) & (f_arr < 255))
    assert transition_pixels


def test_remove_small_noise():
    # 创建带单个孤立噪点的遮罩
    mask_arr = np.zeros((100, 100), dtype=np.uint8)
    # 主体区域 (40x40 = 1600 像素)
    mask_arr[30:70, 30:70] = 255
    # 孤立小噪点 (3x3 = 9 像素)
    mask_arr[10:13, 10:13] = 255
    # 主体内部小空洞 (2x2 = 4 像素)
    mask_arr[45:47, 45:47] = 0

    mask = Image.fromarray(mask_arr, mode="L")
    cleaned = remove_small_noise(mask, min_island_size=50, min_hole_size=50)
    c_arr = np.array(cleaned)

    # 噪点应被清除
    assert np.all(c_arr[10:13, 10:13] == 0)
    # 空洞应被填补
    assert np.all(c_arr[45:47, 45:47] == 255)
    # 主体依然保留
    assert c_arr[50, 50] == 255
