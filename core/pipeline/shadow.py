"""
Matting Studio - 电商物理级阴影发生器
支持双层真实阴影合成:
1. 紧贴底部的硬质接触阴影 (Contact Shadow)
2. 开阔漫反射柔光环境投影 (Ambient Soft Drop Shadow)
3. 镜面微倒影 (Mirror Reflection)
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageFilter


def get_alpha_bottom_contour(alpha_mask: Image.Image, scan_ratio: float = 0.15) -> np.ndarray:
    """
    提取 Alpha 遮罩最底部的实体轮廓区域，用于精确定位与地面接触的接触面
    """
    alpha = np.array(alpha_mask)
    h, w = alpha.shape
    
    # 找到非透明像素的最低行
    y_indices, x_indices = np.where(alpha > 20)
    if len(y_indices) == 0:
        return np.zeros_like(alpha)
    
    y_max = np.max(y_indices)
    scan_h = max(int(h * scan_ratio), 10)
    y_start = max(0, y_max - scan_h)
    
    bottom_strip = np.zeros_like(alpha)
    bottom_strip[y_start : y_max + 1, :] = alpha[y_start : y_max + 1, :]
    return bottom_strip


def generate_contact_shadow(
    alpha_mask: Image.Image,
    offset_y: int = 4,
    blur_radius: int = 3,
    opacity: float = 0.75,
    squash_ratio: float = 0.25,
) -> Image.Image:
    """
    生成紧贴物体底部的接触阴影 (Contact Shadow, 极硬贴合暗角)
    :param alpha_mask: 物体 Alpha 遮罩 (L 模式)
    :param offset_y: 垂直下移像素偏移
    :param blur_radius: 高斯模糊半径 (通常较小 2~4px)
    :param opacity: 阴影最大不透明度 (0.0~1.0)
    :param squash_ratio: 纵向压扁比例 (模拟与地面水平贴合)
    :return: RGBA 格式接触阴影图层 (与 alpha_mask 相同尺寸)
    """
    w, h = alpha_mask.size
    bottom_alpha = get_alpha_bottom_contour(alpha_mask, scan_ratio=0.12)
    
    # 提取非空区域
    ys, xs = np.where(bottom_alpha > 20)
    if len(ys) == 0:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    min_x, max_x = np.min(xs), np.max(xs)
    min_y, max_y = np.min(ys), np.max(ys)
    bw = max(max_x - min_x + 1, 1)
    bh = max(max_y - min_y + 1, 1)
    
    crop_alpha = bottom_alpha[min_y : max_y + 1, min_x : max_x + 1]
    
    # 纵向压扁 (模拟在台面上的投影)
    target_bh = max(int(bh * squash_ratio), 4)
    squashed = cv2.resize(crop_alpha, (bw, target_bh), interpolation=cv2.INTER_LINEAR)
    
    # 施加接触深度浓度
    shadow_alpha = (squashed.astype(np.float32) / 255.0 * (opacity * 255.0)).astype(np.uint8)
    
    # 创建黑色阴影图层
    shadow_img = np.zeros((target_bh, bw, 4), dtype=np.uint8)
    shadow_img[:, :, 3] = shadow_alpha  # 黑色 RGB 为 0，仅 Alpha 变化
    
    pil_shadow = Image.fromarray(shadow_img, mode="RGBA")
    if blur_radius > 0:
        pil_shadow = pil_shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # 贴合回原图尺寸底板
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    paste_y = min(h - target_bh, max_y - target_bh // 2 + offset_y)
    canvas.paste(pil_shadow, (min_x, paste_y), pil_shadow)
    
    return canvas


def generate_ambient_shadow(
    alpha_mask: Image.Image,
    offset_y: int = 12,
    blur_radius: int = 22,
    opacity: float = 0.35,
    scale_y: float = 0.22,
    spread_x: float = 1.15,
) -> Image.Image:
    """
    生成环境柔光漫反射阴影 (Soft Ambient Drop Shadow, 大范围柔和扩散)
    :param alpha_mask: 物体 Alpha 遮罩
    :param offset_y: 纵向偏移
    :param blur_radius: 大半径高斯模糊 (15~35px)
    :param opacity: 阴影最大浓度
    :param scale_y: 纵向投影压扁率
    :param spread_x: 水平微外扩比例
    :return: RGBA 格式柔光阴影图层
    """
    w, h = alpha_mask.size
    alpha = np.array(alpha_mask)
    
    ys, xs = np.where(alpha > 15)
    if len(ys) == 0:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    min_x, max_x = np.min(xs), np.max(xs)
    min_y, max_y = np.min(ys), np.max(ys)
    bw = max_x - min_x + 1
    bh = max_y - min_y + 1
    
    crop_alpha = alpha[min_y : max_y + 1, min_x : max_x + 1]
    
    target_bw = max(int(bw * spread_x), bw)
    target_bh = max(int(bh * scale_y), 10)
    
    squashed = cv2.resize(crop_alpha, (target_bw, target_bh), interpolation=cv2.INTER_LINEAR)
    
    # 沿纵向由深到浅做渐变衰减 (离物体越远越淡)
    fade = np.linspace(1.0, 0.2, target_bh).reshape(-1, 1)
    shadow_alpha = (squashed.astype(np.float32) * fade * opacity).clip(0, 255).astype(np.uint8)
    
    shadow_img = np.zeros((target_bh, target_bw, 4), dtype=np.uint8)
    shadow_img[:, :, 3] = shadow_alpha
    
    pil_shadow = Image.fromarray(shadow_img, mode="RGBA")
    if blur_radius > 0:
        pil_shadow = pil_shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    paste_x = max(0, min_x - (target_bw - bw) // 2)
    paste_y = min(h - target_bh, max_y - target_bh // 3 + offset_y)
    canvas.paste(pil_shadow, (paste_x, paste_y), pil_shadow)
    
    return canvas


def generate_mirror_reflection(
    foreground_rgba: Image.Image,
    opacity: float = 0.25,
    blur_radius: int = 2,
    height_ratio: float = 0.25,
) -> Image.Image:
    """
    生成大理石/镜面展台的倒影效果 (Mirror Reflection)
    :param foreground_rgba: 商品 RGBA 图像
    :param opacity: 倒影初始最大透明度
    :param blur_radius: 磨砂倒影模糊半径
    :param height_ratio: 倒影保留的高度占原图比例 (默认保留底部 25%)
    :return: RGBA 格式倒影图层
    """
    w, h = foreground_rgba.size
    flipped = foreground_rgba.transpose(Image.FLIP_TOP_BOTTOM)
    
    # 获取实体最低点
    alpha = np.array(foreground_rgba.split()[-1])
    ys, _ = np.where(alpha > 15)
    if len(ys) == 0:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    y_max = np.max(ys)
    ref_h = max(int(h * height_ratio), 15)
    
    # 截取翻转后顶部的倒影 (原商品底部)
    crop_ref = flipped.crop((0, h - y_max, w, min(h, h - y_max + ref_h)))
    cw, ch = crop_ref.size
    
    # 构建线性渐变透明度遮罩 (从 opacity 迅速递减到 0)
    grad = np.linspace(opacity * 255.0, 0.0, ch, dtype=np.float32).reshape(-1, 1)
    grad = np.repeat(grad, cw, axis=1)
    
    ref_arr = np.array(crop_ref, dtype=np.float32)
    ref_arr[:, :, 3] = (ref_arr[:, :, 3] * (grad / 255.0)).clip(0, 255)
    ref_arr = ref_arr.astype(np.uint8)
    
    ref_pil = Image.fromarray(ref_arr, mode="RGBA")
    if blur_radius > 0:
        ref_pil = ref_pil.filter(ImageFilter.GaussianBlur(blur_radius))
        
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # 拼接在 y_max 下方
    canvas.paste(ref_pil, (0, y_max), ref_pil)
    return canvas


def apply_ecommerce_shadows(
    foreground_rgba: Image.Image,
    enable_contact: bool = True,
    enable_ambient: bool = True,
    enable_reflection: bool = False,
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    为商品合成全套物理级商用阴影 (返回包含阴影与商品合并后的 RGBA 图像)
    图层顺序 (从下至上):
    1. 漫反射环境柔光阴影 (Ambient Shadow)
    2. 镜面微倒影 (Mirror Reflection)
    3. 贴地接触阴影 (Contact Shadow)
    4. 商品主体 (Foreground Product)
    """
    if foreground_rgba.mode != "RGBA":
        foreground_rgba = foreground_rgba.convert("RGBA")
        
    alpha_mask = foreground_rgba.split()[-1]
    w, h = foreground_rgba.size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    intensity = max(0.0, min(shadow_intensity, 2.0))
    
    # 1. 漫反射柔光阴影
    if enable_ambient and intensity > 0.01:
        amb_shadow = generate_ambient_shadow(
            alpha_mask,
            opacity=min(0.35 * intensity, 0.9),
            blur_radius=20,
        )
        canvas.alpha_composite(amb_shadow)
        
    # 2. 镜面倒影
    if enable_reflection and intensity > 0.01:
        reflection = generate_mirror_reflection(
            foreground_rgba,
            opacity=min(0.22 * intensity, 0.6),
            height_ratio=0.22,
        )
        canvas.alpha_composite(reflection)
        
    # 3. 接触阴影
    if enable_contact and intensity > 0.01:
        cnt_shadow = generate_contact_shadow(
            alpha_mask,
            opacity=min(0.75 * intensity, 1.0),
            blur_radius=3,
        )
        canvas.alpha_composite(cnt_shadow)
        
    # 4. 商品主体
    canvas.alpha_composite(foreground_rgba)
    return canvas
