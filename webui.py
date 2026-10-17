"""
Matting Studio - WebUI 入口启动脚本
使用命令启动:
    python webui.py
或指定端口:
    python webui.py --port 7860 --host 127.0.0.1
"""

import sys
import os
import argparse

# 兼容 Windows GBK 控制台，防止 Unicode 字符 (Emoji) 输出抛出 UnicodeEncodeError
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ui.web.app import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抠图工具 (Matting Studio) - 本地 WebUI")
    parser.add_argument("--host", default="127.0.0.1", help="服务监听地址 (默认: 127.0.0.1, 局域网共享可用 0.0.0.0)")
    parser.add_argument("--port", type=int, default=7860, help="服务端口 (默认: 7860)")
    parser.add_argument("--no-browser", action="store_true", help="启动时不自动打开浏览器")
    parser.add_argument("--share", action="store_true", help="生成 Gradio 公共分享链接 (若需要远程访问)")

    args = parser.parse_args()

    app = create_app()
    print("[Matting Studio] 正在启动 抠图工具 (Matting Studio) WebUI...")
    print(f"[本地访问链接] http://{args.host}:{args.port}")
    app.launch(
        server_name=args.host,
        server_port=args.port,
        inbrowser=not args.no_browser,
        share=args.share,
    )
