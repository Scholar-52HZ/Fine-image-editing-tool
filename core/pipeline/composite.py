"""
Image compositing pipelines (solid color, custom background image).
"""

from __future__ import annotations

import re
from typing import Union, Tuple
from PIL import Image


def parse_color(color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    """
    解析颜色为标准 RGBA (0-255) 四元组
    支持输入格式：
    - "#FFFFFF", "#FFF", "#1E90FF", "#1E90FF80"
    - "red", "blue", "white", "black" 等常见英文名
    - (255, 255, 255) 或 (255, 255, 255, 255)
    """
    NAMED_COLORS = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "red": (255, 0, 0, 255),
        "green": (0, 255, 0, 255),
        "blue": (0, 0, 255, 255),
        "transparent": (0, 0, 0, 0),
        "id_blue": (67, 142, 219, 255),      # 标准证件照蓝
        "id_red": (218, 59, 44, 255),        # 标准证件照红
        "id_white": (255, 255, 255, 255),    # 标准证件照白
        "id_light_blue": (0, 191, 243, 255), # 浅蓝
    }

    if isinstance(color, str):
        color_lower = color.strip().lower()
        if color_lower in NAMED_COLORS:
            return NAMED_COLORS[color_lower]

        hex_match = re.match(r"^#?([0-9a-fA-F]{3,8})$", color.strip())
        if not hex_match:
            raise ValueError(f"无法识别的颜色格式: {color}")
        hex_str = hex_match.group(1)
        if len(hex_str) == 3:  # #RGB
            r, g, b = (int(c * 2, 16) for c in hex_str)
            return (r, g, b, 255)
        elif len(hex_str) == 4:  # #RGBA
            r, g, b, a = (int(c * 2, 16) for c in hex_str)
            return (r, g, b, a)
        elif len(hex_str) == 6:  # #RRGGBB
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_str) == 8:  # #RRGGBBAA
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            a = int(hex_str[6:8], 16)
            return (r, g, b, a)
        else:
            raise ValueError(f"无效的十六进制颜色长度: {color}")

    elif isinstance(color, (tuple, list)):
        if len(color) == 3:
            return (int(color[0]), int(color[1]), int(color[2]), 255)
        elif len(color) == 4:
            return (int(color[0]), int(color[1]), int(color[2]), int(color[3]))
        else:
            raise ValueError(f"颜色元组长度必须为 3 (RGB) 或 4 (RGBA): {color}")

    raise TypeError(f"不支持的颜色类型: {type(color)}")


def composite_with_color(
    foreground: Image.Image,
    color: Union[str, Tuple[int, int, int], Tuple[int, int, int, int]]
) -> Image.Image:
    """
    将 RGBA 前景与纯色背景合成
    :param foreground: RGBA 模式的前景图像
    :param color: 纯色 Hex 字符或元组
    :return: 合成后的图像，若背景完全不透明则返回 RGB 模式，否则返回 RGBA 模式
    """
    if foreground.mode != "RGBA":
        foreground = foreground.convert("RGBA")

    rgba = parse_color(color)
    bg = Image.new("RGBA", foreground.size, rgba)
    composite = Image.alpha_composite(bg, foreground)

    if rgba[3] == 255:
        return composite.convert("RGB")
    return composite


def composite_with_image(
    foreground: Image.Image,
    background: Image.Image,
    mode: str = "cover"
) -> Image.Image:
    """
    将 RGBA 前景与背景图片合成
    :param foreground: RGBA 模式的前景图像
    :param background: 背景图片 (RGB 或 RGBA)
    :param mode: 适配模式:
        - "cover": 保持宽高比放大背景至填满前景区域并居中裁切（默认推荐）
        - "contain": 保持宽高比缩放背景至完全容纳于前景区域中
        - "stretch": 直接拉伸至与前景相同尺寸
    :return: 合成后的 RGB 图像
    """
    if foreground.mode != "RGBA":
        foreground = foreground.convert("RGBA")

    fg_w, fg_h = foreground.size
    bg_w, bg_h = background.size

    if mode == "stretch":
        bg_resized = background.resize((fg_w, fg_h), Image.Resampling.LANCZOS).convert("RGBA")
    elif mode == "cover":
        # 计算覆盖比例
        ratio = max(fg_w / bg_w, fg_h / bg_h)
        new_w = int(bg_w * ratio)
        new_h = int(bg_h * ratio)
        bg_scaled = background.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # 居中裁切
        left = (new_w - fg_w) // 2
        top = (new_h - fg_h) // 2
        bg_resized = bg_scaled.crop((left, top, left + fg_w, top + fg_h)).convert("RGBA")
    elif mode == "contain":
        ratio = min(fg_w / bg_w, fg_h / bg_h)
        new_w = int(bg_w * ratio)
        new_h = int(bg_h * ratio)
        bg_scaled = background.resize((new_w, new_h), Image.Resampling.LANCZOS).convert("RGBA")
        bg_canvas = Image.new("RGBA", (fg_w, fg_h), (0, 0, 0, 255))
        pos_x = (fg_w - new_w) // 2
        pos_y = (fg_h - new_h) // 2
        bg_canvas.paste(bg_scaled, (pos_x, pos_y))
        bg_resized = bg_canvas
    else:
        raise ValueError(f"未知的适配模式: {mode}，支持 'cover' | 'contain' | 'stretch'")

    composite = Image.alpha_composite(bg_resized, foreground)
    return composite.convert("RGB")
