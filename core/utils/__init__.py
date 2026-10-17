"""
Core utility package for Matting Studio.
"""

from core.utils.hardware import (
    HardwareInfo,
    detect_hardware,
    get_device_choices,
    get_execution_providers,
    format_hardware_badge,
)

# Alias for backwards compatibility
get_available_devices = get_device_choices

__all__ = [
    "HardwareInfo",
    "detect_hardware",
    "get_device_choices",
    "get_available_devices",
    "get_execution_providers",
    "format_hardware_badge",
]

