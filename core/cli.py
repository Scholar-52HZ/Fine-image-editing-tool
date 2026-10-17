"""
Command Line Interface (CLI) for Matting Studio.
支持单图抠图、批量处理、背景替换、遮罩单独导出与模型切换。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

# 兼容 Windows GBK 控制台，防止 Unicode 字符输出抛出 UnicodeEncodeError
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.engine.matting_engine import AutoMattingEngine

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def process_single_file(
    engine: AutoMattingEngine,
    input_path: Path,
    output_path: Path,
    bg_color: str | None = None,
    bg_image: str | None = None,
    save_mask_path: Path | None = None,
    alpha_matting: bool = False,
    feather: float = 0.0,
    denoise: bool = False,
    defringe: bool = False,
) -> bool:
    """处理单张图像"""
    try:
        t0 = time.time()
        print(f"[*] 正在处理: {input_path.name} (模型: {engine.current_model}) ...")
        result = engine.predict(
            input_path,
            alpha_matting=alpha_matting,
            feather_radius=feather,
            denoise=denoise,
            defringe=defringe,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if bg_color:
            final_img = result.composite_color(bg_color)
            final_img.save(output_path)
            print(f"    [+] 已合成纯色背景 ({bg_color}) -> {output_path}")
        elif bg_image:
            final_img = result.composite_image(bg_image)
            final_img.save(output_path)
            print(f"    [+] 已合成背景图片 ({bg_image}) -> {output_path}")
        else:
            result.save(output_path)
            print(f"    [+] 已导出透明背景 PNG -> {output_path}")

        if save_mask_path:
            save_mask_path.parent.mkdir(parents=True, exist_ok=True)
            result.save_mask(save_mask_path)
            print(f"    [+] 已保存 Alpha 遮罩 -> {save_mask_path}")

        cost = time.time() - t0
        print(f"    [OK] 完成耗时: {cost:.2f}s")
        return True
    except Exception as e:
        print(f"    [ERROR] 处理失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="python -m core.cli",
        description="🎨 抠图工具 (Matting Studio) - 本地离线高保真智能去背与换底色工具"
    )

    parser.add_argument("input", nargs="?", help="输入图片路径或待批处理的图片文件夹")
    parser.add_argument("-o", "--output", help="输出图片路径或输出目录")
    parser.add_argument(
        "-m", "--model",
        default="bria-rmbg",
        choices=AutoMattingEngine.supported_models(),
        help="选择抠图模型 (默认: bria-rmbg)"
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "gpu"],
        help="计算设备选择 (默认: cpu，可选: gpu 使用 DirectML 显卡硬件加速)"
    )
    parser.add_argument(
        "--bg-color",
        help="合成纯色背景 (支持 Hex 如 '#FFFFFF', '#1E90FF', 或常见名如 'red', 'id_blue')"
    )
    parser.add_argument("--bg-image", help="合成自定义背景图片路径")
    parser.add_argument("--save-mask", help="同时导出 Alpha 灰度遮罩图片路径")
    parser.add_argument(
        "--alpha-matting",
        action="store_true",
        help="启用 Alpha Matting 三值图微调 (对微发丝更细致)"
    )
    parser.add_argument(
        "--feather",
        type=float,
        default=0.0,
        help="边缘高斯平滑羽化半径 (像素，默认 0)"
    )
    parser.add_argument("--denoise", action="store_true", help="启用杂点消除与微小空洞修补")
    parser.add_argument("--defringe", action="store_true", help="启用边缘反光色溢净化")
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="列出所有内置支持的模型与说明"
    )

    args = parser.parse_args()

    if args.list_models:
        print("\n=== 内置支持的开源 SOTA 抠图模型 ===")
        for name, desc in AutoMattingEngine.get_model_descriptions().items():
            print(f"  * {name:<18} : {desc}")
        print()
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件或目录不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    engine = AutoMattingEngine(model_name=args.model, device=args.device)

    # 批处理模式
    if input_path.is_dir():
        out_dir = Path(args.output) if args.output else (input_path / "outputs")
        out_dir.mkdir(parents=True, exist_ok=True)

        img_files: List[Path] = [
            p for p in input_path.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]

        if not img_files:
            print(f"提示: 目录中未找到支持的图片文件: {input_path}")
            return

        print(f"\n🚀 开始批量抠图，共发现 {len(img_files)} 张图片，输出至: {out_dir}")
        success_count = 0
        for idx, img_file in enumerate(img_files, start=1):
            out_file = out_dir / f"{img_file.stem}_matting.png"
            mask_file = (out_dir / f"{img_file.stem}_mask.png") if args.save_mask else None
            print(f"\n[{idx}/{len(img_files)}]")
            ok = process_single_file(
                engine=engine,
                input_path=img_file,
                output_path=out_file,
                bg_color=args.bg_color,
                bg_image=args.bg_image,
                save_mask_path=mask_file,
                alpha_matting=args.alpha_matting,
                feather=args.feather,
                denoise=args.denoise,
                defringe=args.defringe,
            )
            if ok:
                success_count += 1

        print(f"\n🎉 批量处理完成: 成功 {success_count}/{len(img_files)}")

    # 单图处理模式
    else:
        out_file = Path(args.output) if args.output else (input_path.parent / f"{input_path.stem}_matting.png")
        mask_file = Path(args.save_mask) if args.save_mask else None
        ok = process_single_file(
            engine=engine,
            input_path=input_path,
            output_path=out_file,
            bg_color=args.bg_color,
            bg_image=args.bg_image,
            save_mask_path=mask_file,
            alpha_matting=args.alpha_matting,
            feather=args.feather,
            denoise=args.denoise,
            defringe=args.defringe,
        )
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
