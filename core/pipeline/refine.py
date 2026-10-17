"""
Mask refinement and edge post-processing utilities.
提供边缘羽化平滑、去空洞杂点与边缘色溢净化功能。
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageFilter


def feather_mask(mask: Image.Image, radius: float = 1.0) -> Image.Image:
    """
    对 Alpha 遮罩边缘执行轻量高斯羽化，消除阶梯锯齿感
    :param mask: L 模式的灰度遮罩图
    :param radius: 羽化半径 (像素)
    :return: 平滑后的遮罩图
    """
    if radius <= 0:
        return mask
    return mask.filter(ImageFilter.GaussianBlur(radius=radius))


def remove_small_noise(mask: Image.Image, min_island_size: int = 100, min_hole_size: int = 100) -> Image.Image:
    """
    使用 OpenCV 形态学与连通域分析去除孤立噪点与内部微小空洞
    :param mask: L 模式灰度遮罩图
    :param min_island_size: 最小保留孤岛面积（小于该值的孤立高亮噪点将被抹除为背景）
    :param min_hole_size: 最小保留空洞面积（小于该值的微小黑色空洞将被填补为前景）
    :return: 降噪后的遮罩图
    """
    mask_np = np.array(mask, dtype=np.uint8)
    # 二值化
    _, binary = cv2.threshold(mask_np, 127, 255, cv2.THRESH_BINARY)

    # 1. 消除背景中的孤立噪点 (Islands)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    clean_fg = np.zeros_like(binary)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_island_size:
            clean_fg[labels == i] = 255

    # 2. 填补主体内部的小空洞 (Holes)
    inverted = cv2.bitwise_not(clean_fg)
    num_labels_inv, labels_inv, stats_inv, _ = cv2.connectedComponentsWithStats(inverted, connectivity=8)
    for i in range(1, num_labels_inv):
        area = stats_inv[i, cv2.CC_STAT_AREA]
        if area < min_hole_size:
            clean_fg[labels_inv == i] = 255

    # 保持原 mask 的半透明过渡梯度：
    # - 若像素被判定为背景噪点清除 (clean_fg == 0)，置 0
    # - 若像素为空洞被填补 (原 mask_np == 0 但 clean_fg == 255)，填补为 255
    # - 其它有效前景像素保留原有的半透明梯度值
    result_np = np.where(clean_fg == 0, 0, np.where(mask_np == 0, 255, mask_np))
    return Image.fromarray(result_np, mode="L")


def defringe_foreground(foreground: Image.Image, mask: Image.Image, radius: int = 2) -> Image.Image:
    """
    边缘色彩净化 (Defringe / Color Decontamination)
    消除因原背景反光导致的主体边缘（如发丝、衣物边缘）出现的背景色光晕/溢色。
    原理：在半透明边缘处将主体内部的有效颜色向外适度扩散，替换边缘受污染的色彩。
    """
    fg_rgba = foreground.convert("RGBA")
    fg_np = np.array(fg_rgba, dtype=np.uint8)
    alpha = np.array(mask, dtype=np.uint8)

    # 找到半透明边缘过渡区域 (10 < alpha < 245)
    edge_zone = (alpha > 10) & (alpha < 245)
    if not np.any(edge_zone):
        return foreground

    # 提取 RGB 通道
    rgb = fg_np[:, :, :3]
    # 利用形态学膨胀将确定前景 (alpha >= 245) 的颜色适度扩散到半透明过渡区
    solid_mask = (alpha >= 245).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    
    # 对实心区域执行 Inpainting 扩散纯色
    inpaint_mask = ((alpha > 0) & (alpha < 245)).astype(np.uint8)
    cleaned_rgb = cv2.inpaint(rgb, inpaint_mask, inpaintRadius=radius, flags=cv2.INPAINT_TELEA)

    # 在过渡区域融合清理后的颜色
    result_np = fg_np.copy()
    result_np[edge_zone, :3] = cleaned_rgb[edge_zone]
    result_np[:, :, 3] = alpha

    return Image.fromarray(result_np, mode="RGBA")
