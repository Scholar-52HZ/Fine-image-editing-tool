"""
自动化测试套件：电商商品智能工坊与商用全链路工作流
覆盖:
1. 物理级阴影发生器 (core.pipeline.shadow)
2. 画布规范几何自适应 (core.pipeline.framing)
3. 3D 程序化商业展台发生器 (core.pipeline.podium)
4. 语义策划文案裂变引擎 (core.pipeline.copywriter)
5. 多平台海报排版引擎 (core.pipeline.layout)
6. Web 服务端电商全流程自动化与图包打包 (ui.web.service)
"""

import os
import zipfile
import pytest
import numpy as np
from PIL import Image, ImageDraw

from core.pipeline.shadow import (
    generate_contact_shadow,
    generate_ambient_shadow,
    generate_mirror_reflection,
    apply_ecommerce_shadows,
)
from core.pipeline.framing import (
    get_content_bbox,
    crop_to_content,
    fit_to_canvas,
    PLATFORM_SPECS,
)
from core.pipeline.podium import (
    apply_podium,
    PODIUM_GENERATORS,
)
from core.pipeline.copywriter import (
    generate_copy_bundle,
    EcommerceCopyBundle,
)
from core.pipeline.layout import (
    render_ecommerce_layout,
    render_taobao_main,
    render_amazon_main,
    render_red_poster,
    render_detail_banner,
)
from ui.web.service import WebMattingService


@pytest.fixture
def sample_product_rgba() -> Image.Image:
    """生成一个带透明底的模拟商品瓶身图像 (RGBA, 200x400)"""
    img = Image.new("RGBA", (200, 400), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制瓶身主体 (中间 80x250)
    draw.rounded_rectangle([60, 100, 140, 350], radius=15, fill=(40, 140, 220, 255))
    # 绘制瓶盖
    draw.rectangle([80, 50, 120, 100], fill=(210, 215, 225, 255))
    return img


def test_shadow_generators(sample_product_rgba: Image.Image):
    alpha_mask = sample_product_rgba.split()[-1]
    
    # 1. 接触阴影
    contact = generate_contact_shadow(alpha_mask, offset_y=3, blur_radius=2, opacity=0.8)
    assert contact.size == sample_product_rgba.size
    assert contact.mode == "RGBA"
    # 确认生成了非全透明的阴影像素
    alpha_contact = np.array(contact.split()[-1])
    assert np.max(alpha_contact) > 0
    
    # 2. 漫反射环境柔光阴影
    ambient = generate_ambient_shadow(alpha_mask, offset_y=10, blur_radius=15, opacity=0.4)
    assert ambient.size == sample_product_rgba.size
    alpha_ambient = np.array(ambient.split()[-1])
    assert np.max(alpha_ambient) > 0
    
    # 3. 镜面微倒影
    reflection = generate_mirror_reflection(sample_product_rgba, opacity=0.3, blur_radius=1)
    assert reflection.size == sample_product_rgba.size
    alpha_ref = np.array(reflection.split()[-1])
    assert np.max(alpha_ref) > 0
    
    # 4. 全套商用阴影合成
    composite = apply_ecommerce_shadows(
        sample_product_rgba,
        enable_contact=True,
        enable_ambient=True,
        enable_reflection=True,
        shadow_intensity=1.2,
    )
    assert composite.size == sample_product_rgba.size
    assert composite.mode == "RGBA"


def test_framing_adapter(sample_product_rgba: Image.Image):
    # 1. BBox 提取
    bbox = get_content_bbox(sample_product_rgba)
    assert len(bbox) == 4
    min_x, min_y, max_x, max_y = bbox
    assert min_x >= 60 and max_x <= 140
    assert min_y >= 50 and max_y <= 350
    
    # 2. 紧密裁剪
    cropped = crop_to_content(sample_product_rgba, padding=5)
    assert cropped.width <= sample_product_rgba.width
    assert cropped.height <= sample_product_rgba.height
    
    # 3. 画布自适应缩放 (如亚马逊 85% 规范)
    canvas, (px, py, pw, ph) = fit_to_canvas(
        sample_product_rgba,
        target_size=(1000, 1000),
        fill_ratio=0.85,
        anchor="center",
    )
    assert canvas.size == (1000, 1000)
    assert max(pw, ph) == int(1000 * 0.85)
    assert px > 0 and py > 0


def test_podium_generators():
    canvas_size = (800, 800)
    product_bbox = (300, 250, 200, 400)
    
    # 验证各种展台生成正常
    for podium_name in ["marble_cylinder", "nordic_wood", "water_ripple", "studio_geometric"]:
        podium = apply_podium(canvas_size, product_bbox, podium_type=podium_name)
        assert podium.size == canvas_size
        assert podium.mode == "RGBA"
        alpha = np.array(podium.split()[-1])
        assert np.max(alpha) > 0
        
    # none 展台为全透明
    none_podium = apply_podium(canvas_size, product_bbox, podium_type="none")
    assert np.max(np.array(none_podium.split()[-1])) == 0


def test_copywriter_engine():
    copy = generate_copy_bundle(
        product_name="多肽紧致淡纹抗皱面霜",
        product_usage="深层补水 · 熬夜暗沉急救",
        target_audience="25-35岁都市白领",
        brand_tone="极简轻奢",
    )
    assert isinstance(copy, EcommerceCopyBundle)
    assert len(copy.headline) > 0
    assert len(copy.sub_headline) > 0
    assert len(copy.marketing_tags) >= 2
    assert len(copy.detail_bullets) == 3
    assert "白领" in copy.clinical_claim


def test_layout_engine(sample_product_rgba: Image.Image):
    copy = generate_copy_bundle("高定赋活精华", "深层补水", "白领", "极简")
    
    # 1. 淘宝 1:1
    img_tb = render_taobao_main(sample_product_rgba, copy, podium_type="marble_cylinder")
    assert img_tb.size == (800, 800)
    
    # 2. 亚马逊 1:1 纯白底
    img_amz = render_amazon_main(sample_product_rgba, copy)
    assert img_amz.size == (1000, 1000)
    # 验证四个角为纯白 (255, 255, 255)
    assert img_amz.getpixel((5, 5))[:3] == (255, 255, 255)
    
    # 3. 小红书 3:4
    img_red = render_red_poster(sample_product_rgba, copy, podium_type="water_ripple")
    assert img_red.size == (900, 1200)
    
    # 4. 详情页长条
    img_detail = render_detail_banner(sample_product_rgba, copy, podium_type="studio_geometric")
    assert img_detail.size == (750, 1000)


def test_service_ecommerce_suite(sample_product_rgba: Image.Image):
    service = WebMattingService()
    
    # 空输入校验
    tb, amz, red, det, zip_p, msg = service.process_ecommerce_suite(image=None)
    assert tb is None and "请先上传" in msg
    
    # 端到端全套生成 (使用项目内置极速模型 u2netp)
    tb, amz, red, det, zip_p, msg = service.process_ecommerce_suite(
        image=sample_product_rgba,
        model_name="u2netp",
        device="cpu",
        product_name="玻尿酸极光水",
        product_usage="深层补水 · 熬夜急救",
        target_audience="年轻白领",
        brand_tone="极简轻奢",
        selected_platforms=["taobao_main", "amazon_main", "red_poster", "detail_banner"],
        podium_type="marble_cylinder",
        shadow_intensity=1.0,
    )
    
    assert "全套电商资产包生成成功" in msg
    assert tb is not None and tb.size == (800, 800)
    assert amz is not None and amz.size == (1000, 1000)
    assert red is not None and red.size == (900, 1200)
    assert det is not None and det.size == (750, 1000)
    assert zip_p is not None and os.path.exists(zip_p)
    
    # 验证生成的 zip 内部文件完整性
    with zipfile.ZipFile(zip_p, "r") as zf:
        file_names = zf.namelist()
        assert any("00_商品透明原图" in n for n in file_names)
        assert any("01_淘宝天猫主图" in n for n in file_names)
        assert any("02_亚马逊规范白底" in n for n in file_names)
        assert any("03_小红书种草大片" in n for n in file_names)
        assert any("04_详情页核心卖点条" in n for n in file_names)
        
    # 清理测试生成的 zip
    if os.path.exists(zip_p):
        os.remove(zip_p)
