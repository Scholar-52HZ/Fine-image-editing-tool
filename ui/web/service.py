"""
WebUI 业务服务层 - 衔接 Gradio 前端与核心推理引擎 (core.engine / core.pipeline)
"""

from __future__ import annotations

import io
import os
import shutil
import time
import zipfile
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import numpy as np
from PIL import Image, ImageDraw

from core.engine.matting_engine import AutoMattingEngine
from core.pipeline.composite import composite_with_color, composite_with_image
from core.utils.hardware import (
    detect_hardware,
    get_device_choices,
    get_execution_providers,
    format_hardware_badge,
)
from core.utils.model_manager import (
    find_model_path,
    is_model_ready,
    get_model_status,
    get_all_models_status,
    format_model_choice_label,
    download_model,
    LOCAL_MODELS_DIR,
    SUPPORTED_MODELS_META,
)
from core.pipeline.copywriter import generate_copy_bundle, EcommerceCopyBundle
from core.pipeline.layout import render_ecommerce_layout, PLATFORM_SPECS
from core.pipeline.podium import PODIUM_GENERATORS

# 电商展台类型选项
ECOMMERCE_PODIUM_CHOICES: List[Tuple[str, str]] = [
    ("🏛️ 极简大理石圆台 (护肤/香氛/轻奢推荐)", "marble_cylinder"),
    ("🪵 北欧原木托盘 (天然有机/日用个护推荐)", "nordic_wood"),
    ("💧 清透水面波纹光影 (补水/冷饮/水生推荐)", "water_ripple"),
    ("📦 摄影棚极简几何块 (3C数码/机械潮玩推荐)", "studio_geometric"),
    ("⬜ 纯净无展台 (亚马逊极简白底推荐)", "none"),
]

# 电商支持的平台规格清单
ECOMMERCE_PLATFORMS: List[Tuple[str, str]] = [
    ("淘宝/天猫 800×800 爆款展台主图", "taobao_main"),
    ("亚马逊 1000×1000 严格合规白底 (85%留白)", "amazon_main"),
    ("小红书 3:4 (900×1200) 种草封面大片", "red_poster"),
    ("详情页 750px 核心卖点长条", "detail_banner"),
]


# 证件照标准规格字典 (宽 × 高, 单位: 像素, 按 300DPI 标准计算)
ID_PHOTO_SPECS: Dict[str, Tuple[int, int]] = {
    "一寸 (295 × 413 px, 25 × 35 mm)": (295, 413),
    "二寸 (413 × 579 px, 35 × 49 mm)": (413, 579),
    "小一寸 (260 × 378 px, 22 × 32 mm)": (260, 378),
    "大一寸 (390 × 567 px, 33 × 48 mm)": (390, 567),
}

# 证件照经典背景色
ID_PHOTO_COLORS: Dict[str, str] = {
    "标准白底 (#FFFFFF)": "#FFFFFF",
    "标准红底 (#DA3B2C)": "#DA3B2C",
    "标准蓝底 (#438EDB)": "#438EDB",
    "浅天蓝 (#00BFFF)": "#00BFFF",
    "灰白色 (#F2F4F7)": "#F2F4F7",
}

# 常用预设背景色
PRESET_COLORS: Dict[str, str] = {
    "纯白 (#FFFFFF)": "#FFFFFF",
    "正红 (#DA3B2C)": "#DA3B2C",
    "经典蓝 (#438EDB)": "#438EDB",
    "浅蓝 (#00BFFF)": "#00BFFF",
    "商务黑 (#1A1A1A)": "#1A1A1A",
    "中度灰 (#E0E0E0)": "#E0E0E0",
    "清新绿 (#A8E6CF)": "#A8E6CF",
    "淡雅粉 (#FFD3B6)": "#FFD3B6",
}


class WebMattingService:
    """WebUI 业务服务单例管理器"""

    def __init__(self):
        # 严格默认使用 CPU，模型默认极速 u2netp
        self._engine: Optional[AutoMattingEngine] = None
        self._current_model_name: str = "u2netp"
        self._current_device: str = "cpu"

    def get_engine(self, model_name: str = "u2netp", device: str = "cpu") -> AutoMattingEngine:
        """获取或切换引擎会话 (支持模型与设备隔离)"""
        device_norm = (device or "cpu").strip().lower()
        if self._engine is None:
            self._engine = AutoMattingEngine(model_name=model_name, device=device_norm)
            self._current_model_name = model_name
            self._current_device = device_norm
        else:
            if self._current_model_name != model_name:
                self._engine.switch_model(model_name)
                self._current_model_name = model_name
            if self._current_device != device_norm:
                self._engine.switch_device(device_norm)
                self._current_device = device_norm
        return self._engine

    @staticmethod
    def get_device_choices() -> List[Tuple[str, str]]:
        """获取设备选项 (首项严格默认 CPU)"""
        return get_device_choices()

    @staticmethod
    def format_hardware_badge(active_device: str = "cpu") -> str:
        """获取当前硬件状态卡片"""
        return format_hardware_badge(active_device)

    @staticmethod
    def get_model_choices() -> List[Tuple[str, str]]:
        """获取带实时就绪角标的模型选项列表 [(显示文本, 内部代号), ...]"""
        choices = []
        for name in AutoMattingEngine.supported_models():
            label = format_model_choice_label(name)
            choices.append((label, name))
        return choices

    @staticmethod
    def get_model_status_table() -> List[List[str]]:
        """获取全量模型就绪状态清单数据"""
        data = []
        for st in get_all_models_status():
            data.append([
                st["name"],
                st["display_name"],
                st["size_str"],
                st["rec_device"].upper(),
                st["badge"],
                st["local_path"],
            ])
        return data

    @staticmethod
    def get_local_models_path_str() -> str:
        """获取本地 models/ 目录绝对路径"""
        return str(LOCAL_MODELS_DIR.resolve())

    @staticmethod
    def download_model_ui(model_name: str, use_mirror: bool = True) -> str:
        """UI 主动触发模型下载的回调"""
        if not model_name:
            return "⚠️ 请先选择需要下载的模型。"
        if is_model_ready(model_name):
            p = find_model_path(model_name)
            return f"ℹ️ 模型 [{model_name}] 已经处于就绪状态，无需重复下载！路径: `{p}`"
        try:
            path = download_model(model_name, use_mirror=use_mirror)
            return f"🎉 模型 [{model_name}] 下载成功！已就绪于：`{path}`，可在抠图页面直接选用。"
        except Exception as e:
            return f"❌ 下载失败: {str(e)}。\n💡 备选指引：可直接从网盘或 GitHub Releases 下载离线包，解压后拷贝放入 `{LOCAL_MODELS_DIR.resolve()}` 目录即可！"

    def process_single(
        self,
        image: Optional[Image.Image],
        model_name: str = "u2netp",
        device: str = "cpu",

        bg_mode: str = "透明背景 (PNG)",
        preset_color_name: str = "纯白 (#FFFFFF)",
        custom_color: str = "#FFFFFF",
        custom_bg_image: Optional[Image.Image] = None,
        bg_fit_mode: str = "cover",
        feather_radius: float = 0.0,
        alpha_matting: bool = False,
        denoise: bool = True,
        defringe: bool = False,
    ) -> Tuple[Optional[Tuple[Image.Image, Image.Image]], Optional[Image.Image], Optional[Image.Image], str]:
        """
        单图精修核心回调
        :return: (ImageSlider元组(原图,合成图), 最终结果图, 独立Alpha遮罩图, 性能与参数Markdown文本)
        """
        if image is None:
            return None, None, None, "⚠️ 请先上传待抠图的原图。"

        t0 = time.time()
        try:
            engine = self.get_engine(model_name=model_name, device=device)

            # 1. 深度学习推理与边缘后处理 (内置 GPU 显存不足自动降级 CPU 保护)
            result = engine.predict(
                image,
                model_name=model_name,
                device=device,
                alpha_matting=alpha_matting,
                feather_radius=feather_radius,
                denoise=denoise,
                defringe=defringe,
            )

            # 2. 根据背景模式执行合成
            if bg_mode == "透明背景 (PNG)":
                final_img = result.foreground
            elif bg_mode == "预设纯色背景":
                color_hex = PRESET_COLORS.get(preset_color_name, "#FFFFFF")
                final_img = result.composite_color(color_hex)
            elif bg_mode == "自定义颜色":
                color_hex = custom_color or "#FFFFFF"
                final_img = result.composite_color(color_hex)
            elif bg_mode == "自定义背景图":
                if custom_bg_image is not None:
                    final_img = result.composite_image(custom_bg_image, mode=bg_fit_mode)
                else:
                    final_img = result.foreground
            else:
                final_img = result.foreground

            cost_ms = (time.time() - t0) * 1000

            # 组织 ImageSlider 对比元组 (原图RGB, 合成图)
            orig_rgb = result.original
            slider_pair = (orig_rgb, final_img)

            hw = detect_hardware()
            actual_dev = getattr(result, "device_used", device)
            is_gpu = actual_dev in ("gpu", "dml", "cuda") and (hw.has_directml or hw.has_cuda)
            device_label = f"⚡ GPU 硬件加速 ({hw.gpu_name})" if is_gpu else f"💻 CPU 软解模式 ({hw.cpu_name[:22]})"
            fallback_text = getattr(result, "fallback_notice", "")

            metrics = f"""
### ⚡ 处理完成指标
- **计算设备**：`{device_label}`{fallback_text}
- **推理模型**：`{model_name}`
- **图像分辨率**：`{image.width} × {image.height}` 像素
- **总处理耗时**：`{cost_ms:.1f} ms` ({cost_ms/1000:.2f} 秒)
- **后处理特性**：
  - 羽化半径: `{feather_radius} px`
  - Alpha Matting: `{'启用' if alpha_matting else '关闭'}`
  - 噪点空洞修复: `{'启用' if denoise else '关闭'}`
  - 反光色溢净化: `{'启用' if defringe else '关闭'}`
"""
            return slider_pair, final_img, result.mask, metrics
        except Exception as e:
            error_msg = f"""
### ❌ 处理发生异常
- **错误详情**：`{str(e)}`
- **排查建议**：
  1. 若显卡显存较小 (<=4GB)，建议切换为 **💻 CPU 软解模式** 或选用极速轻量模型 **u2netp**；
  2. 若模型权重文件尚未下载完毕，建议选择已内置的 **u2netp** 快速出图。
"""
            return None, None, None, error_msg

    def process_id_photo(
        self,
        image: Optional[Image.Image],
        spec_name: str,
        color_name: str,
        model_name: str,
        device: str = "cpu",
        feather_radius: float = 0.5,
        denoise: bool = True,
    ) -> Tuple[Optional[Image.Image], Optional[Image.Image], str]:
        """
        标准证件照换底与规格裁剪排版
        """
        if image is None:
            return None, None, "⚠️ 请先上传人像图片。"

        t0 = time.time()
        try:
            engine = self.get_engine(model_name=model_name, device=device)
            result = engine.predict(
                image,
                model_name=model_name,
                device=device,
                feather_radius=feather_radius,
                denoise=denoise,
            )

            target_w, target_h = ID_PHOTO_SPECS.get(spec_name, (295, 413))
            bg_hex = ID_PHOTO_COLORS.get(color_name, "#FFFFFF")

            # 换底
            composited = result.composite_color(bg_hex)

            # 居中等比裁剪至证件照比例
            orig_w, orig_h = composited.size
            target_ratio = target_w / target_h
            orig_ratio = orig_w / orig_h

            if orig_ratio > target_ratio:
                new_w = int(orig_h * target_ratio)
                left = (orig_w - new_w) // 2
                cropped = composited.crop((left, 0, left + new_w, orig_h))
            else:
                new_h = int(orig_w / target_ratio)
                top = max(0, int((orig_h - new_h) * 0.15))
                cropped = composited.crop((0, top, orig_w, top + new_h))

            id_photo = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            cost_ms = (time.time() - t0) * 1000

            hw = detect_hardware()
            actual_dev = getattr(result, "device_used", device)
            is_gpu = actual_dev in ("gpu", "dml", "cuda") and (hw.has_directml or hw.has_cuda)
            device_label = f"⚡ GPU 加速 ({hw.gpu_name})" if is_gpu else f"💻 CPU 软解 (默认)"
            fallback_text = getattr(result, "fallback_notice", "")

            info = f"""
### 🪪 证件照生成成功
- **计算设备**：`{device_label}`{fallback_text}
- **规格名称**：`{spec_name}`
- **输出尺寸**：`{target_w} × {target_h}` 像素 (300 DPI 冲印级)
- **底色模式**：`{color_name}`
- **生成耗时**：`{cost_ms:.1f} ms`
"""
            return id_photo, result.foreground, info
        except Exception as e:
            return None, None, f"### ❌ 证件照生成异常: {str(e)}"


    def process_batch(
        self,
        files: Optional[List[Any]],
        model_name: str,
        device: str = "cpu",
        bg_mode: str = "透明背景 (PNG)",
        preset_color_name: str = "纯白 (#FFFFFF)",
        custom_color: str = "#FFFFFF",
        feather_radius: float = 0.0,
        denoise: bool = True,
    ) -> Tuple[Optional[str], List[List[Any]], str]:
        """
        批量抠图流水线处理
        """
        if not files:
            return None, [], "⚠️ 请先上传至少一张图片或图片包。"

        t0 = time.time()
        engine = self.get_engine(model_name=model_name, device=device)

        batch_id = int(time.time() * 1000)
        temp_dir = Path(".ai/artifacts") / f"batch_{batch_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        table_data: List[List[Any]] = []
        success_count = 0

        for idx, file_obj in enumerate(files, start=1):
            file_path = Path(file_obj.name if hasattr(file_obj, "name") else str(file_obj))
            file_name = file_path.name

            try:
                sub_t0 = time.time()
                pil_img = Image.open(file_path)
                w, h = pil_img.size

                result = engine.predict(
                    pil_img,
                    model_name=model_name,
                    device=device,
                    feather_radius=feather_radius,
                    denoise=denoise,
                )

                if bg_mode == "预设纯色背景":
                    color_hex = PRESET_COLORS.get(preset_color_name, "#FFFFFF")
                    out_img = result.composite_color(color_hex)
                    ext = "jpg" if color_hex == "#FFFFFF" else "png"
                elif bg_mode == "自定义颜色":
                    color_hex = custom_color or "#FFFFFF"
                    out_img = result.composite_color(color_hex)
                    ext = "png"
                else:  # 透明背景
                    out_img = result.foreground
                    ext = "png"

                out_filename = f"{file_path.stem}_matting.{ext}"
                out_path = temp_dir / out_filename
                out_img.save(out_path)

                sub_cost = (time.time() - sub_t0) * 1000
                table_data.append([file_name, f"{w}×{h}", "✅ 成功", f"{sub_cost:.1f}ms", out_filename])
                success_count += 1
            except Exception as e:
                table_data.append([file_name, "-", f"❌ 失败: {str(e)[:30]}", "-", "-"])

        # 压缩打包成 zip
        zip_path = temp_dir.parent / f"batch_matting_{batch_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in temp_dir.glob("*.*"):
                zf.write(item, arcname=item.name)

        # 清理中间小文件
        shutil.rmtree(temp_dir, ignore_errors=True)

        total_cost = time.time() - t0
        summary = f"🎉 批量处理完毕！共处理 **{len(files)}** 张，成功 **{success_count}** 张，失败 **{len(files) - success_count}** 张，总耗时 **{total_cost:.2f}** 秒。"
        return str(zip_path), table_data, summary

    @staticmethod
    def create_sample_image() -> str:
        """动态生成一张用于快速测试的示例几何/人像图"""
        sample_path = Path(".ai/artifacts/sample_demo.png")
        if sample_path.exists():
            return str(sample_path)

        sample_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (400, 400), (45, 120, 85))
        draw = ImageDraw.Draw(img)
        # 绘制主体圆球与高光
        draw.ellipse((100, 100, 300, 300), fill=(230, 80, 50), outline=(255, 255, 255), width=4)
        draw.ellipse((150, 130, 210, 190), fill=(255, 180, 160))
        img.save(sample_path)
        return str(sample_path)

    def process_ecommerce_suite(
        self,
        image: Optional[Image.Image],
        model_name: str = "u2netp",
        device: str = "cpu",
        product_name: str = "极光赋活紧致修护精华液",
        product_usage: str = "深层补水 · 熬夜暗沉急救",
        target_audience: str = "25-35岁都市白领 / 熬夜党",
        brand_tone: str = "极简轻奢",
        selected_platforms: Optional[List[str]] = None,
        podium_type: str = "marble_cylinder",
        shadow_intensity: float = 1.0,
        feather_radius: int = 1,
        defringe: bool = True,
    ) -> Tuple[Optional[Image.Image], Optional[Image.Image], Optional[Image.Image], Optional[Image.Image], Optional[str], str]:
        """
        一键全自动生成全套电商商用图包 (淘宝1:1 / 亚马逊85%白底 / 小红书3:4 / 详情页长条)
        """
        if image is None:
            return None, None, None, None, None, "⚠️ 请先上传一张商品原图。"

        if not is_model_ready(model_name):
            return (
                None,
                None,
                None,
                None,
                None,
                f"⚠️ 模型 [{model_name}] 尚未下载就绪。请前往【📦 离线模型管理】页面点击一键下载，或选用内置极速模型 `u2netp`。",
            )

        if not selected_platforms:
            selected_platforms = ["taobao_main", "amazon_main", "red_poster", "detail_banner"]

        t0 = time.time()
        try:
            # 1. 核心抠图与去反光溢色
            engine = self.get_engine(model_name=model_name, device=device)
            result = engine.predict(image, feather_radius=feather_radius, defringe=defringe)
            fg = result.foreground

            # 2. 商业文案策划裂变
            copy_bundle = generate_copy_bundle(
                product_name=product_name,
                product_usage=product_usage,
                target_audience=target_audience,
                brand_tone=brand_tone,
            )

            # 3. 建立临时输出目录并多平台渲染
            batch_id = int(time.time() * 1000)
            out_dir = Path("outputs") / f"ecommerce_{batch_id}"
            out_dir.mkdir(parents=True, exist_ok=True)

            fg.save(out_dir / "00_商品透明原图_100保真.png")

            img_taobao: Optional[Image.Image] = None
            img_amazon: Optional[Image.Image] = None
            img_red: Optional[Image.Image] = None
            img_detail: Optional[Image.Image] = None

            if "taobao_main" in selected_platforms:
                img_taobao = render_ecommerce_layout(
                    fg, copy_bundle, platform_id="taobao_main", podium_type=podium_type, shadow_intensity=shadow_intensity
                )
                img_taobao.save(out_dir / "01_淘宝天猫主图_800x800.png")

            if "amazon_main" in selected_platforms:
                img_amazon = render_ecommerce_layout(
                    fg, copy_bundle, platform_id="amazon_main", podium_type="none", shadow_intensity=shadow_intensity
                )
                # 亚马逊规范白底存为高质量 JPG
                img_amazon.convert("RGB").save(out_dir / "02_亚马逊规范白底_1000x1000.jpg", quality=95)

            if "red_poster" in selected_platforms:
                img_red = render_ecommerce_layout(
                    fg, copy_bundle, platform_id="red_poster", podium_type=podium_type, shadow_intensity=shadow_intensity
                )
                img_red.save(out_dir / "03_小红书种草大片_900x1200.png")

            if "detail_banner" in selected_platforms:
                img_detail = render_ecommerce_layout(
                    fg, copy_bundle, platform_id="detail_banner", podium_type=podium_type, shadow_intensity=shadow_intensity
                )
                img_detail.save(out_dir / "04_详情页核心卖点条_750x1000.png")

            # 4. 压缩打包成 zip
            zip_path = Path("outputs") / f"ecommerce_bundle_{batch_id}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_item in sorted(out_dir.glob("*.*")):
                    zf.write(file_item, arcname=file_item.name)

            shutil.rmtree(out_dir, ignore_errors=True)

            total_cost_ms = (time.time() - t0) * 1000
            summary = (
                f"🎉 **全套电商资产包生成成功！**\n"
                f"- ⏱️ 总耗时: **{total_cost_ms:.1f} ms**\n"
                f"- 🧠 模型与算力: **{model_name}** ({device.upper()} 模式)\n"
                f"- 📐 已生成规格: **{len(selected_platforms)}** 项 (淘宝/亚马逊/小红书/详情页)\n"
                f"- 💎 主体保真度: **100% 原始细节锁定**，已自动消除反光色溢并生成物理级真实光影。"
            )

            return img_taobao, img_amazon, img_red, img_detail, str(zip_path), summary

        except Exception as e:
            err_msg = f"❌ 电商图包生成失败: {str(e)}"
            return None, None, None, None, None, err_msg

