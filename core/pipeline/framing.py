"""
Matting Studio - 电商画布几何自适应与平台规范留白适配器 (Auto-Framing)
支持淘宝 1:1、亚马逊 85% 规范留白、小红书 3:4、详情页长条尺寸规范
"""

from __future__ import annotations

import numpy as np
from PIL import Image

# 平台常用几何规格常量
PLATFORM_SPECS = {
    "taobao_main": {
        "id": "taobao_main",
        "name": "淘宝/天猫 1:1 展台主图",
        "size": (800, 800),
        "fill_ratio": 0.75,
        "anchor": "center_bottom",
        "aspect_ratio": "1:1",
    },
    "amazon_main": {
        "id": "amazon_main",
        "name": "亚马逊 85% 严格规范白底图",
        "size": (1000, 1000),
        "fill_ratio": 0.85,
        "anchor": "center",
        "aspect_ratio": "1:1",
    },
    "red_poster": {
        "id": "red_poster",
        "name": "小红书 3:4 种草大片",
        "size": (900, 1200),
        "fill_ratio": 0.62,
        "anchor": "center",
        "aspect_ratio": "3:4",
    },
    "detail_banner": {
        "id": "detail_banner",
        "name": "详情页核心卖点条 (750px)",
        "size": (750, 1000),
        "fill_ratio": 0.55,
        "anchor": "left_center",
        "aspect_ratio": "3:4",
    },
}


def get_content_bbox(image: Image.Image, alpha_threshold: int = 15) -> tuple[int, int, int, int]:
    """
    计算非透明主体的紧密外接矩形边界 (min_x, min_y, max_x, max_y)
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    alpha = np.array(image.split()[-1])
    ys, xs = np.where(alpha > alpha_threshold)
    
    if len(ys) == 0:
        return (0, 0, image.width, image.height)
        
    return (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))


def crop_to_content(image: Image.Image, padding: int = 0) -> Image.Image:
    """
    将图像紧贴主体非透明边界进行裁剪，可添加安全留白 padding
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    min_x, min_y, max_x, max_y = get_content_bbox(image)
    w, h = image.size
    
    crop_x1 = max(0, min_x - padding)
    crop_y1 = max(0, min_y - padding)
    crop_x2 = min(w, max_x + 1 + padding)
    crop_y2 = min(h, max_y + 1 + padding)
    
    return image.crop((crop_x1, crop_y1, crop_x2, crop_y2))


def fit_to_canvas(
    image: Image.Image,
    target_size: tuple[int, int] = (800, 800),
    fill_ratio: float = 0.85,
    anchor: str = "center",
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """
    按平台规范将商品等比例自适应缩放到目标画布中
    :param image: 输入商品 RGBA 图像
    :param target_size: 画布目标分辨率 (width, height)
    :param fill_ratio: 主体占画布主轴的比例 (如 0.85 代表亚马逊 85% 规范)
    :param anchor: 对齐锚点 ('center', 'center_bottom', 'bottom', 'left_center')
    :return: (合成后的 RGBA 画布, 商品在画布上的实际粘贴位置坐标 (paste_x, paste_y, scaled_w, scaled_h))
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")
        
    # 1. 紧密裁剪去多余透明边框
    tight_img = crop_to_content(image)
    orig_w, orig_h = tight_img.size
    
    canvas_w, canvas_h = target_size
    
    # 2. 计算等比例缩放系数
    max_target_w = canvas_w * fill_ratio
    max_target_h = canvas_h * fill_ratio
    scale = min(max_target_w / orig_w, max_target_h / orig_h)
    
    scaled_w = max(int(orig_w * scale), 1)
    scaled_h = max(int(orig_h * scale), 1)
    
    resized_img = tight_img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    
    # 3. 计算坐标偏移
    if anchor == "center":
        paste_x = (canvas_w - scaled_w) // 2
        paste_y = (canvas_h - scaled_h) // 2
    elif anchor == "center_bottom":
        paste_x = (canvas_w - scaled_w) // 2
        # 底部留白约 15% 画布高度 (为展台与阴影预留基准面)
        bottom_margin = int(canvas_h * 0.16)
        paste_y = max(0, canvas_h - scaled_h - bottom_margin)
    elif anchor == "bottom":
        paste_x = (canvas_w - scaled_w) // 2
        paste_y = canvas_h - scaled_h
    elif anchor == "left_center":
        # 靠左 12% 边距，垂直居中
        paste_x = int(canvas_w * 0.10)
        paste_y = (canvas_h - scaled_h) // 2
    else:
        paste_x = (canvas_w - scaled_w) // 2
        paste_y = (canvas_h - scaled_h) // 2
        
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.paste(resized_img, (paste_x, paste_y), resized_img)
    
    return canvas, (paste_x, paste_y, scaled_w, scaled_h)
