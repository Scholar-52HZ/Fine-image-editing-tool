"""
Matting Studio - 程序化 3D 商业展台发生器 (Podium Generator)
支持大理石圆台、北欧原木托盘、水面光影微波台、极简摄影棚几何块
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def create_marble_cylinder(
    canvas_size: tuple[int, int],
    product_bbox: tuple[int, int, int, int],
) -> Image.Image:
    """
    生成高光微距大理石圆柱展台 (适合美妆、香氛、轻奢饰品)
    """
    cw, ch = canvas_size
    px, py, pw, ph = product_bbox
    
    podium_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(podium_layer)
    
    # 展台中心与定位
    x_center = px + pw // 2
    y_base = py + ph
    
    podium_w = max(int(pw * 1.55), int(cw * 0.48))
    rx = podium_w // 2
    ry = max(int(rx * 0.28), 12)  # 椭圆透视长短轴比
    cylinder_h = max(int(ch * 0.12), 25)
    
    # 1. 展台侧面立柱 (柱身)
    side_box = [x_center - rx, y_base, x_center + rx, y_base + cylinder_h]
    # 侧面渐变：左侧暗、中部高光反光、右侧暗
    side_img = np.zeros((cylinder_h, podium_w, 4), dtype=np.uint8)
    gradient_x = np.sin(np.linspace(0, np.pi, podium_w)).reshape(1, -1)
    base_lum = (210 + gradient_x * 38).clip(0, 255).astype(np.uint8)
    
    side_img[:, :, 0] = base_lum - 2  # R
    side_img[:, :, 1] = base_lum      # G
    side_img[:, :, 2] = base_lum + 4  # B (微冷调高级灰)
    side_img[:, :, 3] = 255
    
    pil_side = Image.fromarray(side_img, mode="RGBA")
    podium_layer.paste(pil_side, (x_center - rx, y_base))
    
    # 底面封闭椭圆 (柱底)
    draw.ellipse(
        [x_center - rx, y_base + cylinder_h - ry, x_center + rx, y_base + cylinder_h + ry],
        fill=(195, 198, 205, 255),
    )
    
    # 2. 顶面透视椭圆 (台面)
    top_ellipse = [x_center - rx, y_base - ry, x_center + rx, y_base + ry]
    draw.ellipse(top_ellipse, fill=(244, 246, 250, 255), outline=(225, 228, 235, 255), width=1)
    
    # 顶面边缘高光细线
    draw.arc(top_ellipse, start=180, end=360, fill=(255, 255, 255, 220), width=2)
    
    # 展台底部投影 (展台投在地面上的微暗影)
    podium_shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(podium_shadow)
    s_draw.ellipse(
        [x_center - int(rx * 1.1), y_base + cylinder_h - int(ry * 0.6), x_center + int(rx * 1.1), y_base + cylinder_h + int(ry * 1.2)],
        fill=(0, 0, 0, 60),
    )
    podium_shadow = podium_shadow.filter(ImageFilter.GaussianBlur(15))
    
    # 合成阴影与展台
    final_podium = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    final_podium.alpha_composite(podium_shadow)
    final_podium.alpha_composite(podium_layer)
    return final_podium


def create_nordic_wood(
    canvas_size: tuple[int, int],
    product_bbox: tuple[int, int, int, int],
) -> Image.Image:
    """
    生成北欧温润原木托盘展台 (适合天然有机、食品个护、日用家居)
    """
    cw, ch = canvas_size
    px, py, pw, ph = product_bbox
    
    podium_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(podium_layer)
    
    x_center = px + pw // 2
    y_base = py + ph
    
    podium_w = max(int(pw * 1.6), int(cw * 0.50))
    rx = podium_w // 2
    ry = max(int(rx * 0.26), 10)
    cylinder_h = max(int(ch * 0.08), 18)
    
    # 侧面木纹色
    side_img = np.zeros((cylinder_h, podium_w, 4), dtype=np.uint8)
    gradient_x = np.sin(np.linspace(0, np.pi, podium_w)).reshape(1, -1)
    
    # 原木色基调
    side_img[:, :, 0] = (195 + gradient_x * 25).clip(0, 255).astype(np.uint8)  # R
    side_img[:, :, 1] = (160 + gradient_x * 22).clip(0, 255).astype(np.uint8)  # G
    side_img[:, :, 2] = (120 + gradient_x * 18).clip(0, 255).astype(np.uint8)  # B
    side_img[:, :, 3] = 255
    
    pil_side = Image.fromarray(side_img, mode="RGBA")
    podium_layer.paste(pil_side, (x_center - rx, y_base))
    
    # 顶面暖木色
    draw.ellipse(
        [x_center - rx, y_base - ry, x_center + rx, y_base + ry],
        fill=(226, 196, 162, 255),
        outline=(205, 175, 140, 255),
        width=1,
    )
    draw.arc([x_center - rx, y_base - ry, x_center + rx, y_base + ry], start=180, end=360, fill=(250, 230, 210, 200), width=2)
    
    # 底部环境光
    podium_shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(podium_shadow)
    s_draw.ellipse(
        [x_center - int(rx * 1.05), y_base + cylinder_h - int(ry * 0.5), x_center + int(rx * 1.05), y_base + cylinder_h + int(ry * 1.1)],
        fill=(0, 0, 0, 50),
    )
    podium_shadow = podium_shadow.filter(ImageFilter.GaussianBlur(12))
    
    final_podium = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    final_podium.alpha_composite(podium_shadow)
    final_podium.alpha_composite(podium_layer)
    return final_podium


def create_water_ripple(
    canvas_size: tuple[int, int],
    product_bbox: tuple[int, int, int, int],
) -> Image.Image:
    """
    生成水面微波与清透倒影展台 (适合爽肤水、补水凝露、夏日冷饮)
    """
    cw, ch = canvas_size
    px, py, pw, ph = product_bbox
    
    x_center = px + pw // 2
    y_base = py + ph
    
    ripple_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ripple_layer)
    
    podium_w = max(int(pw * 1.8), int(cw * 0.60))
    rx = podium_w // 2
    ry = int(rx * 0.28)
    
    # 同心微波水环
    for step in range(3, 0, -1):
        cur_rx = int(rx * (step / 3.0))
        cur_ry = int(ry * (step / 3.0))
        alpha = int(45 * (1.0 - step / 4.0))
        draw.ellipse(
            [x_center - cur_rx, y_base - cur_ry, x_center + cur_rx, y_base + cur_ry],
            fill=(180, 230, 250, alpha),
            outline=(210, 245, 255, alpha * 2),
            width=2,
        )
        
    ripple_layer = ripple_layer.filter(ImageFilter.GaussianBlur(3))
    return ripple_layer


def create_studio_geometric(
    canvas_size: tuple[int, int],
    product_bbox: tuple[int, int, int, int],
) -> Image.Image:
    """
    生成摄影棚极简几何块展台 (适合 3C 数码、机械、硬核潮品)
    """
    cw, ch = canvas_size
    px, py, pw, ph = product_bbox
    
    x_center = px + pw // 2
    y_base = py + ph
    
    geo_w = max(int(pw * 1.4), int(cw * 0.45))
    geo_h = max(int(ch * 0.10), 20)
    geo_depth = int(geo_h * 0.6)
    
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x1 = x_center - geo_w // 2
    x2 = x_center + geo_w // 2
    
    # 立方块正面
    draw.rectangle([x1, y_base, x2, y_base + geo_h], fill=(230, 232, 238, 255), outline=(210, 215, 222, 255))
    # 立方块顶面
    top_poly = [
        (x1, y_base),
        (x1 + geo_depth // 2, y_base - geo_depth // 2),
        (x2 + geo_depth // 2, y_base - geo_depth // 2),
        (x2, y_base),
    ]
    draw.polygon(top_poly, fill=(248, 249, 252, 255), outline=(225, 228, 235, 255))
    # 侧立面
    side_poly = [
        (x2, y_base),
        (x2 + geo_depth // 2, y_base - geo_depth // 2),
        (x2 + geo_depth // 2, y_base + geo_h - geo_depth // 2),
        (x2, y_base + geo_h),
    ]
    draw.polygon(side_poly, fill=(210, 214, 222, 255), outline=(195, 200, 210, 255))
    
    # 底部环境影
    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rectangle([x1 - 10, y_base + geo_h - 5, x2 + geo_depth // 2 + 10, y_base + geo_h + 15], fill=(0, 0, 0, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    
    final_geo = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    final_geo.alpha_composite(shadow)
    final_geo.alpha_composite(layer)
    return final_geo


PODIUM_GENERATORS = {
    "marble_cylinder": create_marble_cylinder,
    "nordic_wood": create_nordic_wood,
    "water_ripple": create_water_ripple,
    "studio_geometric": create_studio_geometric,
}


def apply_podium(
    canvas_size: tuple[int, int],
    product_bbox: tuple[int, int, int, int],
    podium_type: str = "marble_cylinder",
) -> Image.Image:
    """
    统一入口：根据展台类型生成底座图层
    :param canvas_size: 画布大小 (w, h)
    :param product_bbox: 商品在画布上的位置与尺寸 (x, y, w, h)
    :param podium_type: 展台类型 ('none', 'marble_cylinder', 'nordic_wood', 'water_ripple', 'studio_geometric')
    :return: 对应的 RGBA 展台图层 (透明底)
    """
    if podium_type == "none" or podium_type not in PODIUM_GENERATORS:
        return Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        
    generator = PODIUM_GENERATORS[podium_type]
    return generator(canvas_size, product_bbox)
