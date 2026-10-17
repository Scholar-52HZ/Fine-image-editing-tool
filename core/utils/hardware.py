"""
Hardware detection and device dispatch utilities for Matting Studio.
自动探测 CPU、GPU (DirectML/CUDA) 与可用推理提供者，并提供用户自主配置映射。
"""

from __future__ import annotations

import os
import platform
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import onnxruntime


@dataclass
class HardwareInfo:
    """系统硬件与推理运行时状态实体"""
    cpu_name: str = "未知 CPU"
    cpu_cores: int = 4
    cpu_threads: int = 8
    total_ram_gb: float = 0.0
    free_ram_gb: float = 0.0
    gpu_name: str = "无独立显卡"
    gpu_vram_mb: float = 0.0
    has_gpu: bool = False
    has_directml: bool = False
    has_cuda: bool = False
    providers: List[str] = field(default_factory=list)


_CACHED_HW_INFO: Optional[HardwareInfo] = None


def detect_hardware(force_refresh: bool = False) -> HardwareInfo:
    """
    探测当前主机的 CPU、GPU、内存以及 ONNX Runtime 支持情况 (带进程内缓存)
    """
    global _CACHED_HW_INFO
    if _CACHED_HW_INFO is not None and not force_refresh:
        return _CACHED_HW_INFO

    info = HardwareInfo()

    # 1. 检测 ONNX Runtime 提供者
    try:
        info.providers = onnxruntime.get_available_providers()
        info.has_directml = "DmlExecutionProvider" in info.providers
        info.has_cuda = "CUDAExecutionProvider" in info.providers
    except Exception:
        info.providers = ["CPUExecutionProvider"]

    # 2. 检测 CPU 基本信息
    try:
        info.cpu_name = platform.processor() or "Generic x86_64 CPU"
        info.cpu_threads = os.cpu_count() or 4
        info.cpu_cores = max(1, info.cpu_threads // 2)
    except Exception:
        pass

    # 3. 在 Windows 上通过 WMI 探测精确 CPU 与独显信息 (带超时安全保护)
    if platform.system().lower() == "windows":
        try:
            # 探测 CPU 详情
            cpu_cmd = "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cpu_cmd], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    data = data[0]
                if data.get("Name"):
                    info.cpu_name = str(data["Name"]).strip()
                if data.get("NumberOfCores"):
                    info.cpu_cores = int(data["NumberOfCores"])
                if data.get("NumberOfLogicalProcessors"):
                    info.cpu_threads = int(data["NumberOfLogicalProcessors"])
        except Exception:
            pass

        try:
            # 探测 GPU 详情 (优先查找 NVIDIA / AMD 独显)
            gpu_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", gpu_cmd], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                gpu_list = json.loads(res.stdout)
                if isinstance(gpu_list, dict):
                    gpu_list = [gpu_list]
                for gpu in gpu_list:
                    name = str(gpu.get("Name", "")).strip()
                    # 排除虚拟显卡
                    if any(virt in name.lower() for virt in ["virtual", "oray", "todesk", "gameviewer"]):
                        continue
                    if any(kw in name.lower() for kw in ["nvidia", "geforce", "rtx", "gtx", "radeon", "intel"]):
                        vram = round(gpu.get("AdapterRAM", 0) / (1024 * 1024), 1) if gpu.get("AdapterRAM") else 0.0
                        info.gpu_name = name
                        info.gpu_vram_mb = vram
                        info.has_gpu = True
                        if any(kw in name.lower() for kw in ["nvidia", "geforce", "rtx", "gtx", "radeon"]):
                            break  # 找到主力独显则停止搜索
        except Exception:
            pass

        try:
            # 探测物理内存
            mem_cmd = "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", mem_cmd], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                mem = json.loads(res.stdout)
                info.total_ram_gb = round(mem.get("TotalVisibleMemorySize", 0) / (1024 * 1024), 2)
                info.free_ram_gb = round(mem.get("FreePhysicalMemory", 0) / (1024 * 1024), 2)
        except Exception:
            pass

    _CACHED_HW_INFO = info
    return info


def get_device_choices() -> List[Tuple[str, str]]:
    """
    获取供 WebUI / 用户选择的硬件设备选项列表
    按照要求：首项严格为 CPU，并作为系统默认选项！
    :return: [(内部键值, 展示标签), ...]
    """
    hw = detect_hardware()
    choices = [("cpu", f"💻 CPU 处理器模式 (默认 · {hw.cpu_name[:22]}...)")]

    if hw.has_directml:
        gpu_display = hw.gpu_name if hw.gpu_name and hw.gpu_name != "无独立显卡" else "DirectX 12 独显"
        choices.append(("gpu", f"⚡ GPU 硬件加速 ({gpu_display} · DirectML 提速10~20倍)"))
    elif hw.has_cuda:
        choices.append(("gpu", f"⚡ GPU 硬件加速 ({hw.gpu_name} · CUDA)"))

    return choices


get_available_devices = get_device_choices


def get_execution_providers(device: str = "cpu") -> List[str]:
    """
    根据用户指定的设备返回 ONNX Runtime Execution Providers 列表
    :param device: "cpu" (默认) 或 "gpu" / "dml"
    :return: providers 列表
    """
    device_norm = (device or "cpu").strip().lower()
    hw = detect_hardware()

    if device_norm in ("gpu", "dml", "cuda"):
        if hw.has_directml:
            return ["DmlExecutionProvider", "CPUExecutionProvider"]
        elif hw.has_cuda:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            # 回退到 CPU
            return ["CPUExecutionProvider"]

    # 默认使用 CPU
    return ["CPUExecutionProvider"]


def format_hardware_badge(active_device: str = "cpu") -> str:
    """
    格式化当前硬件运行状态的 Markdown 横幅
    """
    hw = detect_hardware()
    active_norm = active_device.strip().lower()

    if active_norm in ("gpu", "dml", "cuda") and (hw.has_directml or hw.has_cuda):
        mode_text = f"⚡ **GPU 硬件加速已启用** (`{hw.gpu_name}`)"
        speed_text = "极速 (单图约 0.5~1.2 秒)"
        tag_color = "🟢"
    else:
        mode_text = f"💻 **CPU 处理器软解运行中 (默认)** (`{hw.cpu_name}`)"
        speed_text = "标准 (单图约 10~20 秒，零显存开销)"
        tag_color = "🔵"

    return f"""
> {tag_color} **当前运行状态**：{mode_text} ｜ 预计速度：**{speed_text}** ｜ 可用内存：`{hw.free_ram_gb:.1f} GB / {hw.total_ram_gb:.1f} GB`
"""
