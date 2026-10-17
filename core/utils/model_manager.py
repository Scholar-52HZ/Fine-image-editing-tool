"""
Model Asset Management and Resolution System for Matting Studio.
支持项目内置模型 (u2netp)、本地 models/ 离线模型包、用户缓存 ~/.rembg/ 多级优先解析，
以及基于自有 GitHub Releases + 国内加速镜像的自主下载与状态探测。
"""

from __future__ import annotations

import os
import sys
import logging
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)

# 项目根目录与模型目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_MODELS_DIR = PROJECT_ROOT / "models"
LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# 用户仓库配置 (自有 Release 源)
USER_REPO = "Scholar-52HZ/Fine-image-editing-tool"
USER_RELEASE_TAG = "v0.1.0-models"

# 国内高速镜像代理前缀列表 (按可用性优先排序)
MIRROR_PROXIES = [
    "https://ghfast.top/",
    "https://ghproxy.net/",
    "https://gh-proxy.com/",
]


@dataclass
class ModelMeta:
    """模型元数据实体"""
    name: str
    display_name: str
    size_mb: float
    filename: str
    recommended_device: str  # "gpu" or "cpu"
    is_builtin: bool = False
    description: str = ""

    @property
    def direct_user_release_url(self) -> str:
        """自有 GitHub Releases 直链"""
        return f"https://github.com/{USER_REPO}/releases/download/{USER_RELEASE_TAG}/{self.filename}"

    @property
    def upstream_fallback_url(self) -> str:
        """上游原作者备份源"""
        return f"https://github.com/danielgatis/rembg/releases/download/v0.0.0/{self.filename}"

    def get_download_urls(self, use_mirror: bool = True) -> List[str]:
        """获取带有国内加速镜像的下载候选 URL 列表"""
        urls = []
        if use_mirror:
            for proxy in MIRROR_PROXIES:
                urls.append(f"{proxy}{self.direct_user_release_url}")
        # 直连自有 Release
        urls.append(self.direct_user_release_url)
        # 上游备份镜像
        if use_mirror:
            for proxy in MIRROR_PROXIES:
                urls.append(f"{proxy}{self.upstream_fallback_url}")
        urls.append(self.upstream_fallback_url)
        return urls


# 全量受支持模型元数据注册表
SUPPORTED_MODELS_META: Dict[str, ModelMeta] = {
    "u2netp": ModelMeta(
        name="u2netp",
        display_name="U-2-Net Portable",
        size_mb=4.4,
        filename="u2netp.onnx",
        recommended_device="gpu",
        is_builtin=True,
        description="极轻量级基准模型 (项目内置 · 4.5MB · CPU/GPU 极速出图)",
    ),
    "bria-rmbg": ModelMeta(
        name="bria-rmbg",
        display_name="Bria RMBG 2.0",
        size_mb=1024.0,
        filename="bria-rmbg-2.0.onnx",
        recommended_device="cpu",
        is_builtin=False,
        description="高保真发丝级精修模型 (1.0GB · 专精电商人像发丝 · 建议 CPU 软解)",
    ),
    "silueta": ModelMeta(
        name="silueta",
        display_name="Silueta",
        size_mb=44.0,
        filename="silueta.onnx",
        recommended_device="gpu",
        is_builtin=False,
        description="超轻量紧凑模型 (44MB · 平衡速度与轮廓完整度)",
    ),
    "u2net": ModelMeta(
        name="u2net",
        display_name="U-2-Net Full",
        size_mb=176.0,
        filename="u2net.onnx",
        recommended_device="cpu",
        is_builtin=False,
        description="经典显著性高精度模型 (176MB · 边缘分割细腻全面)",
    ),
    "birefnet-portrait": ModelMeta(
        name="birefnet-portrait",
        display_name="BiRefNet Portrait",
        size_mb=240.0,
        filename="birefnet-portrait.onnx",
        recommended_device="cpu",
        is_builtin=False,
        description="双边参考人像专精模型 (240MB · 专攻极细发丝与毛发)",
    ),
    "birefnet-general": ModelMeta(
        name="birefnet-general",
        display_name="BiRefNet General",
        size_mb=480.0,
        filename="birefnet-general.onnx",
        recommended_device="cpu",
        is_builtin=False,
        description="双边参考通用高分辨率模型 (480MB · 复杂背景泛化能力强)",
    ),
    "isnet-general-use": ModelMeta(
        name="isnet-general-use",
        display_name="IS-Net General",
        size_mb=174.0,
        filename="isnet-general-use.onnx",
        recommended_device="cpu",
        is_builtin=False,
        description="通用目标物体分割模型 (174MB · 物体与商品精准去背)",
    ),
}


def find_model_path(model_name: str) -> Optional[Path]:
    """
    多级优先检索本地模型文件：
    1. 项目本地 models/ 根目录 (如 models/u2netp.onnx)
    2. 项目本地 models/ 下的同名子目录 (如 models/bria-rmbg/bria-rmbg.onnx)
    3. 系统全局 ~/.rembg/models/<name>/<filename>
    4. 系统全局 ~/.u2net/<filename>
    """
    meta = SUPPORTED_MODELS_META.get(model_name)
    filenames = [f"{model_name}.onnx"]
    if meta:
        filenames.append(meta.filename)
    filenames = list(dict.fromkeys(filenames))  # 去重

    # 1. 检索项目本地 models 目录
    for fname in filenames:
        p1 = LOCAL_MODELS_DIR / fname
        if p1.exists() and p1.stat().st_size > 1024 * 100:  # 大于 100KB
            return p1
        p2 = LOCAL_MODELS_DIR / model_name / fname
        if p2.exists() and p2.stat().st_size > 1024 * 100:
            return p2

    # 2. 检索系统用户目录 ~/.rembg/models/
    user_home = Path.home()
    rembg_home = Path(os.getenv("REMBG_HOME", user_home / ".rembg"))
    for fname in filenames:
        p3 = rembg_home / "models" / model_name / fname
        if p3.exists() and p3.stat().st_size > 1024 * 100:
            return p3
        p4 = rembg_home / "models" / fname
        if p4.exists() and p4.stat().st_size > 1024 * 100:
            return p4

    # 3. 检索旧版 ~/.u2net/
    u2net_home = Path(os.getenv("U2NET_HOME", user_home / ".u2net"))
    for fname in filenames:
        p5 = u2net_home / fname
        if p5.exists() and p5.stat().st_size > 1024 * 100:
            return p5

    return None


def is_model_ready(model_name: str) -> bool:
    """检测指定模型是否在本地已就绪"""
    return find_model_path(model_name) is not None


def get_model_status(model_name: str) -> Dict[str, any]:
    """获取指定模型的全面就绪状态"""
    meta = SUPPORTED_MODELS_META.get(model_name)
    path = find_model_path(model_name)
    is_ready = path is not None

    if meta:
        size_str = f"{meta.size_mb:.1f} MB" if meta.size_mb < 1000 else f"{meta.size_mb/1024:.2f} GB"
        display_name = meta.display_name
        is_builtin = meta.is_builtin
        rec_device = meta.recommended_device
    else:
        size_str = "--"
        display_name = model_name
        is_builtin = False
        rec_device = "cpu"

    if is_ready:
        if is_builtin and "models" in str(path):
            badge = f"✅ 已就绪 (项目内置 · {size_str})"
            status_text = "项目内置"
        else:
            badge = f"✅ 已就绪 (本地离线 · {size_str})"
            status_text = "本地已下载"
    else:
        badge = f"⬇️ 未就绪 (需下载 · {size_str})"
        status_text = "待下载"

    return {
        "name": model_name,
        "display_name": display_name,
        "is_ready": is_ready,
        "is_builtin": is_builtin,
        "local_path": str(path) if path else "未就绪",
        "size_str": size_str,
        "badge": badge,
        "status_text": status_text,
        "rec_device": rec_device,
    }


def get_all_models_status() -> List[Dict[str, any]]:
    """获取所有支持模型的就绪状态列表"""
    return [get_model_status(name) for name in SUPPORTED_MODELS_META.keys()]


def format_model_choice_label(model_name: str) -> str:
    """为 WebUI 下拉框生成带清晰角标的文本"""
    status = get_model_status(model_name)
    meta = SUPPORTED_MODELS_META.get(model_name)
    tag = status["badge"]
    rec_text = "⚡ GPU/CPU秒抠" if status["rec_device"] == "gpu" else "💻 建议CPU"
    return f"{model_name} —— {tag} ｜ {rec_text}"


def download_model(
    model_name: str,
    target_dir: Optional[Path] = None,
    use_mirror: bool = True,
    progress_callback: Optional[Callable[[int, int, float], None]] = None,
) -> Path:
    """
    主动下载指定模型，支持国内高速镜像与进度回调
    :param model_name: 模型代号
    :param target_dir: 目标保存目录 (默认保存至项目 models/)
    :param use_mirror: 是否使用国内高速镜像前缀
    :param progress_callback: 进度回调 (downloaded_bytes, total_bytes, percent)
    :return: 下载完成的文件本地路径
    """
    meta = SUPPORTED_MODELS_META.get(model_name)
    if not meta:
        raise ValueError(f"未知的模型代号: {model_name}")

    dest_dir = target_dir or LOCAL_MODELS_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"{model_name}.onnx"

    urls = meta.get_download_urls(use_mirror=use_mirror)
    last_err = None

    for url in urls:
        logger.info(f"正在尝试从源下载模型 [{model_name}]: {url}")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MattingStudio/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as response, open(dest_file, "wb") as out_file:
                total_length = response.getheader("content-length")
                total_bytes = int(total_length) if total_length else int(meta.size_mb * 1024 * 1024)
                downloaded = 0
                block_size = 64 * 1024  # 64 KB

                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)
                    percent = (downloaded / total_bytes) * 100 if total_bytes > 0 else 0.0
                    if progress_callback:
                        progress_callback(downloaded, total_bytes, percent)

            # 校验文件大小
            if dest_file.exists() and dest_file.stat().st_size > 1024 * 100:
                logger.info(f"模型 [{model_name}] 成功下载至 {dest_file} ({dest_file.stat().st_size / (1024*1024):.1f} MB)")
                return dest_file
            else:
                if dest_file.exists():
                    dest_file.unlink()
        except Exception as e:
            logger.warning(f"从源 {url} 下载失败: {e}，正在尝试下一个备用源...")
            if dest_file.exists():
                try:
                    dest_file.unlink()
                except Exception:
                    pass
            last_err = e

    raise RuntimeError(f"模型 [{model_name}] 下载失败，所有候选源均不可用。最后错误: {last_err}")


# ==============================================================================
# 动态注入 rembg 的 BaseSession.resolve_existing，实现项目本地 models/ 免改动识别
# ==============================================================================
def patch_rembg_resolver():
    """
    向 rembg 会话基类注入本地 models/ 优先解析逻辑。
    使 rembg 原生调用完全透明感知项目本地存放的模型文件，彻底免于重复下载。
    """
    try:
        from rembg.sessions.base import BaseSession

        if getattr(BaseSession, "_matting_studio_patched", False):
            return

        original_resolve = BaseSession.resolve_existing

        @classmethod
        def patched_resolve_existing(cls, fname, *args, **kwargs):
            model_name = cls.name(*args, **kwargs)
            # 1. 优先使用我们的多级检索
            local_path = find_model_path(model_name)
            if local_path and local_path.exists():
                return str(local_path)
            # 2. 回退到原 rembg 的检索
            return original_resolve(fname, *args, **kwargs)

        BaseSession.resolve_existing = patched_resolve_existing
        BaseSession._matting_studio_patched = True
        logger.debug("已成功挂载 rembg 本地 models/ 优先解析钩子。")
    except Exception as e:
        logger.warning(f"挂载 rembg 钩子时发生异常: {e}")


# 导入模块时自动执行一次安全挂钩
patch_rembg_resolver()
