"""
Matting Studio - 多平台规格式海报与长图自动排版渲染器 (E-Commerce Layout Engine)
基于 PIL 高性能图像绘制引擎，纯本地离线秒级渲染：
1. 淘宝/天猫 800x800 爆款展台主图 (带利益点与角标)
2. 亚马逊 1000x1000 严格规范合规纯白底图 (85% 留白 + 真实接触漫反射阴影)
3. 小红书 3:4 (900x1200) 种草大片海报 (氛围背景 + 痛点大字)
4. 详情页 750x1000 核心卖点长条模块
"""

from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

from core.pipeline.framing import fit_to_canvas, PLATFORM_SPECS
from core.pipeline.shadow import apply_ecommerce_shadows
from core.pipeline.podium import apply_podium
from core.pipeline.copywriter import EcommerceCopyBundle


def get_font(size: int = 24, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    """获取跨平台中文字体，优先寻找 Windows 微软雅黑与黑体"""
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_linear_gradient(size: tuple[int, int], top_color: tuple[int, int, int], bottom_color: tuple[int, int, int]) -> Image.Image:
    """生成平滑竖向双色渐变底板"""
    w, h = size
    r1, g1, b1 = top_color
    r2, g2, b2 = bottom_color
    
    y = np.linspace(0, 1, h).reshape(-1, 1)
    r = (r1 + (r2 - r1) * y).astype(np.uint8)
    g = (g1 + (g2 - g1) * y).astype(np.uint8)
    b = (b1 + (b2 - b1) * y).astype(np.uint8)
    
    grad = np.zeros((h, w, 3), dtype=np.uint8)
    grad[:, :, 0] = np.repeat(r, w, axis=1)
    grad[:, :, 1] = np.repeat(g, w, axis=1)
    grad[:, :, 2] = np.repeat(b, w, axis=1)
    
    return Image.fromarray(grad, mode="RGB").convert("RGBA")


def render_taobao_main(
    product_rgba: Image.Image,
    copy: EcommerceCopyBundle,
    podium_type: str = "marble_cylinder",
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    渲染淘宝/天猫 800x800 爆款主图
    """
    spec = PLATFORM_SPECS["taobao_main"]
    cw, ch = spec["size"]
    
    # 1. 高端冷灰微渐变背景
    bg = create_linear_gradient((cw, ch), (248, 249, 252), (232, 235, 242))
    
    # 2. 几何自适应缩放与定位
    framed_product, (px, py, pw, ph) = fit_to_canvas(
        product_rgba,
        target_size=(cw, ch),
        fill_ratio=spec["fill_ratio"],
        anchor=spec["anchor"],
    )
    
    # 3. 展台
    podium_layer = apply_podium((cw, ch), (px, py, pw, ph), podium_type=podium_type)
    bg.alpha_composite(podium_layer)
    
    # 4. 真实物理阴影 + 商品主体
    shadowed_product = apply_ecommerce_shadows(
        framed_product,
        enable_contact=True,
        enable_ambient=True,
        enable_reflection=(podium_type == "marble_cylinder"),
        shadow_intensity=shadow_intensity,
    )
    bg.alpha_composite(shadowed_product)
    
    # 5. 顶栏营销文案与角标排版
    draw = ImageDraw.Draw(bg)
    font_badge = get_font(20, bold=True)
    font_sub = get_font(16, bold=False)
    
    # 左上角促销胶囊标签
    badge_text = f"🔥 {copy.benefit_badge} · {copy.sub_headline[:10]}"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox[2] - bbox[0] + 24, bbox[3] - bbox[1] + 14
    
    draw.rounded_rectangle([25, 25, 25 + bw, 25 + bh], radius=8, fill=(235, 55, 65, 245))
    draw.text((37, 25 + 7), badge_text, fill=(255, 255, 255, 255), font=font_badge)
    
    # 右上角品质角标
    tag_text = "官方正品"
    draw.rounded_rectangle([cw - 110, 25, cw - 25, 25 + 34], radius=6, fill=(30, 35, 45, 200))
    draw.text((cw - 100, 31), tag_text, fill=(255, 255, 255, 240), font=font_sub)
    
    return bg


def render_amazon_main(
    product_rgba: Image.Image,
    copy: EcommerceCopyBundle,
    podium_type: str = "none",
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    渲染亚马逊严格规范 1000x1000 纯白底图 (85% 留白 + 真实接触暗角，严禁文字/水印/外展台)
    """
    spec = PLATFORM_SPECS["amazon_main"]
    cw, ch = spec["size"]
    
    # 亚马逊要求 100% 纯白底板 (RGB 255, 255, 255)
    bg = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
    
    # 85% 黄金比例居中缩放
    framed_product, (px, py, pw, ph) = fit_to_canvas(
        product_rgba,
        target_size=(cw, ch),
        fill_ratio=spec["fill_ratio"],
        anchor=spec["anchor"],
    )
    
    # 亚马逊仅允许逼真的轻微地面接触与漫反射阴影，不得有花哨展台与文字
    shadowed_product = apply_ecommerce_shadows(
        framed_product,
        enable_contact=True,
        enable_ambient=True,
        enable_reflection=False,
        shadow_intensity=0.85 * shadow_intensity,
    )
    bg.alpha_composite(shadowed_product)
    return bg


def render_red_poster(
    product_rgba: Image.Image,
    copy: EcommerceCopyBundle,
    podium_type: str = "water_ripple",
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    渲染小红书 3:4 (900x1200) 种草封面大片 (社交痛点大字 + 氛围生活展台 + 标签)
    """
    spec = PLATFORM_SPECS["red_poster"]
    cw, ch = spec["size"]
    
    # 暖调居家晨光莫兰迪粉白渐变
    bg = create_linear_gradient((cw, ch), (254, 245, 245), (250, 248, 244))
    
    # 几何缩放 (留出顶部文案与底部标签空间)
    framed_product, (px, py, pw, ph) = fit_to_canvas(
        product_rgba,
        target_size=(cw, ch),
        fill_ratio=spec["fill_ratio"],
        anchor="center",
    )
    
    # 展台
    podium_layer = apply_podium((cw, ch), (px, py, pw, ph), podium_type=podium_type)
    bg.alpha_composite(podium_layer)
    
    # 阴影与主体
    shadowed_product = apply_ecommerce_shadows(
        framed_product,
        enable_contact=True,
        enable_ambient=True,
        enable_reflection=(podium_type != "none"),
        shadow_intensity=shadow_intensity,
    )
    bg.alpha_composite(shadowed_product)
    
    draw = ImageDraw.Draw(bg)
    font_hl = get_font(34, bold=True)
    font_sub = get_font(22, bold=False)
    font_tag = get_font(18, bold=True)
    
    # 顶部痛点醒目大字
    hl_text = f"✨ {copy.headline}"
    bbox_hl = draw.textbbox((0, 0), hl_text, font=font_hl)
    hw, hh = bbox_hl[2] - bbox_hl[0] + 32, bbox_hl[3] - bbox_hl[1] + 16
    draw.rounded_rectangle([40, 50, 40 + hw, 50 + hh], radius=8, fill=(230, 45, 75, 245))
    draw.text((56, 58), hl_text, fill=(255, 255, 255, 255), font=font_hl)
    
    # 副标题
    draw.text((45, 50 + hh + 14), copy.sub_headline, fill=(50, 55, 65, 230), font=font_sub)
    
    # 底部种草标签 pills
    cur_x = 45
    tag_y = ch - 80
    for tag in copy.marketing_tags:
        t_str = f"#{tag}"
        t_box = draw.textbbox((0, 0), t_str, font=font_tag)
        tw = t_box[2] - t_box[0] + 24
        draw.rounded_rectangle([cur_x, tag_y, cur_x + tw, tag_y + 36], radius=18, fill=(255, 255, 255, 220), outline=(220, 225, 235, 255))
        draw.text((cur_x + 12, tag_y + 7), t_str, fill=(80, 85, 95, 255), font=font_tag)
        cur_x += tw + 14
        
    return bg


def render_detail_banner(
    product_rgba: Image.Image,
    copy: EcommerceCopyBundle,
    podium_type: str = "studio_geometric",
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    渲染详情页 750x1000 核心卖点长条模块
    """
    spec = PLATFORM_SPECS["detail_banner"]
    cw, ch = spec["size"]
    
    bg = Image.new("RGBA", (cw, ch), (250, 251, 254, 255))
    draw = ImageDraw.Draw(bg)
    
    font_title = get_font(28, bold=True)
    font_sub = get_font(18, bold=False)
    font_bullet = get_font(20, bold=True)
    font_claim = get_font(16, bold=False)
    
    # 顶部主标题
    draw.text((40, 40), "三维立体核心专研拆解", fill=(25, 30, 45, 255), font=font_title)
    draw.text((40, 80), f"{copy.product_name} · 专研科技机理", fill=(110, 115, 130, 255), font=font_sub)
    draw.line([(40, 115), (cw - 40, 115)], fill=(225, 230, 240, 255), width=2)
    
    # 左侧放置自适应商品图
    framed_product, (px, py, pw, ph) = fit_to_canvas(
        product_rgba,
        target_size=(cw, ch),
        fill_ratio=spec["fill_ratio"],
        anchor="left_center",
    )
    podium_layer = apply_podium((cw, ch), (px, py, pw, ph), podium_type=podium_type)
    bg.alpha_composite(podium_layer)
    
    shadowed_product = apply_ecommerce_shadows(
        framed_product,
        enable_contact=True,
        enable_ambient=True,
        shadow_intensity=shadow_intensity,
    )
    bg.alpha_composite(shadowed_product)
    
    # 重新获取 draw (在 alpha_composite 之后)
    draw = ImageDraw.Draw(bg)
    
    # 右侧排版 3 条卖点打钩项
    bx = cw // 2 + 10
    by = ch // 3
    for bullet in copy.detail_bullets:
        draw.text((bx, by), bullet, fill=(35, 120, 75, 255), font=font_bullet)
        by += 60
        
    # 底部背书说明卡片
    draw.rounded_rectangle([40, ch - 120, cw - 40, ch - 40], radius=10, fill=(240, 244, 252, 255), outline=(215, 225, 242, 255))
    draw.text((60, ch - 90), f"📌 {copy.clinical_claim}", fill=(70, 80, 100, 255), font=font_claim)
    
    return bg


RENDERERS = {
    "taobao_main": render_taobao_main,
    "amazon_main": render_amazon_main,
    "red_poster": render_red_poster,
    "detail_banner": render_detail_banner,
}


def render_ecommerce_layout(
    product_rgba: Image.Image,
    copy: EcommerceCopyBundle,
    platform_id: str = "taobao_main",
    podium_type: str = "marble_cylinder",
    shadow_intensity: float = 1.0,
) -> Image.Image:
    """
    多平台规格式排版渲染统一入口
    :param product_rgba: 已去背透明商品图 (RGBA)
    :param copy: 结构化商业文案
    :param platform_id: 平台代号 ('taobao_main', 'amazon_main', 'red_poster', 'detail_banner')
    :param podium_type: 展台类型
    :param shadow_intensity: 阴影强度 (0.0~2.0)
    :return: 渲染好的平台商用图像 (RGBA)
    """
    if platform_id not in RENDERERS:
        platform_id = "taobao_main"
    renderer = RENDERERS[platform_id]
    return renderer(product_rgba, copy, podium_type=podium_type, shadow_intensity=shadow_intensity)
