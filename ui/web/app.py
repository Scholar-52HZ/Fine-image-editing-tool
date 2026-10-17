"""
Gradio WebUI Application for Matting Studio.
包含单图精修工坊、批量处理流水线、证件照快速换底与模型管理四大功能中心。
已集成硬件状态动态探测与 CPU/GPU 自主配置功能 (严格默认 CPU)。
"""

from __future__ import annotations

import gradio as gr
from PIL import Image

from core.engine.matting_engine import AutoMattingEngine
from ui.web.service import (
    WebMattingService,
    ID_PHOTO_SPECS,
    ID_PHOTO_COLORS,
    PRESET_COLORS,
    ECOMMERCE_PODIUM_CHOICES,
    ECOMMERCE_PLATFORMS,
)

service = WebMattingService()


def toggle_bg_controls(bg_mode: str):
    """根据选择的背景模式动态显示或隐藏对应的控制组件"""
    show_preset = bg_mode == "预设纯色背景"
    show_custom_color = bg_mode == "自定义颜色"
    show_custom_bg = bg_mode == "自定义背景图"

    return (
        gr.update(visible=show_preset),
        gr.update(visible=show_custom_color),
        gr.update(visible=show_custom_bg),
        gr.update(visible=show_custom_bg),
    )


def create_app() -> gr.Blocks:
    """构建 WebUI 核心界面"""
    # 获取带实时状态角标的模型选项列表 [(展示文本, 内部代号)]
    model_choices = service.get_model_choices()
    default_model = "u2netp"

    # 获取当前主机的硬件设备选项，首项严格为 CPU (默认)
    device_choices = service.get_device_choices()
    default_device = "cpu"

    with gr.Blocks(title="🎨 抠图工具 (Matting Studio)") as demo:
        gr.Markdown(
            """
# 🎨 抠图工具 (Matting Studio)
### 本地离线 · SOTA 深度学习模型 · 发丝级精细去背 · 纯色换底 · 批量极速处理
---
"""
        )

        # 硬件状态实时看板
        hw_badge = gr.Markdown(service.format_hardware_badge(active_device=default_device))

        with gr.Tabs():
            # =========================================================
            # Tab 1: 单图精细抠图与背景替换工坊
            # =========================================================
            with gr.Tab("🎨 单图精修工坊 (Single Matting)"):
                with gr.Row():
                    with gr.Column(scale=4):
                        input_img = gr.Image(
                            label="📥 待抠图片 (支持拖拽/点击/Ctrl+V粘贴)",
                            type="pil",
                            sources=["upload", "clipboard"],
                        )

                        sample_btn = gr.Button("💡 载入快速测试样例图", size="sm")

                        with gr.Group():
                            device_radio = gr.Radio(
                                choices=[(label, val) for val, label in device_choices],
                                value=default_device,
                                label="⚙️ 计算硬件选择 (主动配置 · 默认 CPU)",
                                info="默认使用 CPU 软解；如需 10~20 倍极速处理，可主动切换至 GPU 独显加速",
                            )

                            model_dropdown = gr.Dropdown(
                                choices=model_choices,
                                value=default_model,
                                label="🧠 抠图模型选型 (动态检测本地就绪状态)",
                                info="默认推荐 u2netp (极速全能 · 项目内置免下载)；发丝级精修可选 bria-rmbg (建议CPU)",
                            )

                            bg_mode_radio = gr.Radio(

                                choices=["透明背景 (PNG)", "预设纯色背景", "自定义颜色", "自定义背景图"],
                                value="透明背景 (PNG)",
                                label="🖼️ 输出背景类型",
                            )

                            preset_color_dropdown = gr.Dropdown(
                                choices=list(PRESET_COLORS.keys()),
                                value="纯白 (#FFFFFF)",
                                label="🎨 预设纯色选项",
                                visible=False,
                            )

                            custom_color_picker = gr.ColorPicker(
                                value="#FFFFFF",
                                label="🎨 自定义色盘选择",
                                visible=False,
                            )

                            custom_bg_img = gr.Image(
                                label="🏞️ 自定义背景图片",
                                type="pil",
                                visible=False,
                            )

                            bg_fit_dropdown = gr.Dropdown(
                                choices=["cover", "contain", "stretch"],
                                value="cover",
                                label="适配填充模式 (cover=填满居中, contain=完整包含, stretch=拉伸)",
                                visible=False,
                            )

                        with gr.Accordion("⚙️ 发丝级高级微调参数", open=False):
                            feather_slider = gr.Slider(
                                minimum=0.0,
                                maximum=5.0,
                                value=0.0,
                                step=0.1,
                                label="边缘平滑羽化半径 (px)",
                                info="平滑边缘阶梯锯齿",
                            )
                            alpha_matting_chk = gr.Checkbox(
                                value=False,
                                label="启用 Alpha Matting 三值图精细化 (对极细碎发丝更精细，推理耗时稍长)",
                            )
                            denoise_chk = gr.Checkbox(
                                value=True,
                                label="启用孤立杂点消除与微小空洞自动修补",
                            )
                            defringe_chk = gr.Checkbox(
                                value=False,
                                label="启用边缘反光色溢净化 (消除原背景在发丝/衣物边缘留下的反光色环)",
                            )

                        btn_run_single = gr.Button("🚀 立即开始抠图 / 换背景", variant="primary", size="lg")

                    with gr.Column(scale=6):
                        slider_output = gr.ImageSlider(
                            label="🔍 交互式卷帘对比 (原图 vs 抠图)",
                            type="pil",
                        )

                        with gr.Tabs():
                            with gr.Tab("🖼️ 最终合成图"):
                                result_output = gr.Image(label="最终图像 (可右键另存或直接下载)", type="pil", format="png")
                            with gr.Tab("🎭 Alpha 遮罩图"):
                                mask_output = gr.Image(label="单通道 Alpha 蒙版图", type="pil", format="png")

                        metrics_output = gr.Markdown()

                # 事件绑定: 硬件选择切换动态更新看板
                device_radio.change(
                    fn=service.format_hardware_badge,
                    inputs=[device_radio],
                    outputs=[hw_badge],
                )

                # 事件绑定: 动态切换背景控制器显示状态
                bg_mode_radio.change(
                    fn=toggle_bg_controls,
                    inputs=[bg_mode_radio],
                    outputs=[preset_color_dropdown, custom_color_picker, custom_bg_img, bg_fit_dropdown],
                )

                # 事件绑定: 载入样例图
                sample_btn.click(
                    fn=lambda: Image.open(service.create_sample_image()),
                    outputs=[input_img],
                )

                # 事件绑定: 触发单图处理
                btn_run_single.click(
                    fn=service.process_single,
                    inputs=[
                        input_img,
                        model_dropdown,
                        device_radio,
                        bg_mode_radio,
                        preset_color_dropdown,
                        custom_color_picker,
                        custom_bg_img,
                        bg_fit_dropdown,
                        feather_slider,
                        alpha_matting_chk,
                        denoise_chk,
                        defringe_chk,
                    ],
                    outputs=[slider_output, result_output, mask_output, metrics_output],
                )

            # =========================================================
            # Tab 2: 批量抠图流水线工坊
            # =========================================================
            with gr.Tab("⚡ 批量抠图流水线 (Batch Studio)"):
                gr.Markdown("### 🚀 支持批量选择或拖入多个图片文件，自动流水线处理并打包下载")
                with gr.Row():
                    with gr.Column(scale=4):
                        batch_files_input = gr.File(
                            label="📁 批量图片上传 (可多选)",
                            file_count="multiple",
                            file_types=["image"],
                        )
                        batch_device_radio = gr.Radio(
                            choices=[(label, val) for val, label in device_choices],
                            value=default_device,
                            label="⚙️ 批量计算设备 (默认 CPU · 建议切换 GPU 极速)",
                        )
                        batch_model_dropdown = gr.Dropdown(
                            choices=model_choices,
                            value="u2netp",
                            label="🧠 批量处理模型 (推荐快速轻量的 u2netp 或 silueta)",
                        )
                        batch_bg_mode = gr.Radio(
                            choices=["透明背景 (PNG)", "预设纯色背景", "自定义颜色"],
                            value="透明背景 (PNG)",
                            label="🖼️ 批量统一背景",
                        )
                        batch_preset_color = gr.Dropdown(
                            choices=list(PRESET_COLORS.keys()),
                            value="纯白 (#FFFFFF)",
                            label="预设底色",
                            visible=False,
                        )
                        batch_custom_color = gr.ColorPicker(
                            value="#FFFFFF",
                            label="自定义取色",
                            visible=False,
                        )
                        with gr.Accordion("⚙️ 批量后处理微调", open=False):
                            batch_feather = gr.Slider(0.0, 5.0, value=0.0, step=0.1, label="边缘平滑羽化 (px)")
                            batch_denoise = gr.Checkbox(value=True, label="自动消除杂点")

                        btn_run_batch = gr.Button("⚡ 开始批量全自动处理", variant="primary", size="lg")

                    with gr.Column(scale=6):
                        batch_zip_output = gr.File(label="📦 一键打包下载全部处理结果 (.zip)")
                        batch_table_output = gr.Dataframe(
                            headers=["文件名", "原图尺寸", "状态", "耗时", "产物名"],
                            label="📋 批处理执行明细",
                        )
                        batch_summary_output = gr.Markdown()

                # 事件绑定: 批量背景模式切换
                batch_bg_mode.change(
                    fn=lambda m: (gr.update(visible=m == "预设纯色背景"), gr.update(visible=m == "自定义颜色")),
                    inputs=[batch_bg_mode],
                    outputs=[batch_preset_color, batch_custom_color],
                )

                # 事件绑定: 启动批量任务
                btn_run_batch.click(
                    fn=service.process_batch,
                    inputs=[
                        batch_files_input,
                        batch_model_dropdown,
                        batch_device_radio,
                        batch_bg_mode,
                        batch_preset_color,
                        batch_custom_color,
                        batch_feather,
                        batch_denoise,
                    ],
                    outputs=[batch_zip_output, batch_table_output, batch_summary_output],
                )

            # =========================================================
            # Tab 3: 标准证件照一键换底与排版工坊
            # =========================================================
            with gr.Tab("🪪 证件照工坊 (ID Photo Studio)"):
                gr.Markdown("### 📷 人像智能识别、300DPI 标准冲印规格裁剪与官方标准底色替换")
                with gr.Row():
                    with gr.Column(scale=4):
                        id_input_img = gr.Image(label="📥 上传原始人像照片", type="pil", sources=["upload", "clipboard"])
                        id_device_radio = gr.Radio(
                            choices=[(label, val) for val, label in device_choices],
                            value=default_device,
                            label="⚙️ 证件照计算设备 (默认 CPU)",
                        )
                        id_spec_dropdown = gr.Dropdown(
                            choices=list(ID_PHOTO_SPECS.keys()),
                            value="一寸 (295 × 413 px, 25 × 35 mm)",
                            label="📐 证件照规格选择",
                        )
                        id_color_radio = gr.Radio(
                            choices=list(ID_PHOTO_COLORS.keys()),
                            value="标准白底 (#FFFFFF)",
                            label="🎨 证件照官方底色",
                        )
                        id_model_dropdown = gr.Dropdown(
                            choices=model_choices,
                            value=default_model,
                            label="🧠 推理模型",
                        )
                        with gr.Accordion("⚙️ 人像发丝微调", open=False):
                            id_feather = gr.Slider(0.0, 3.0, value=0.5, step=0.1, label="发丝柔和羽化 (px)")
                            id_denoise = gr.Checkbox(value=True, label="背景杂点降噪")

                        btn_run_id = gr.Button("🪪 立即生成官方标准证件照", variant="primary", size="lg")

                    with gr.Column(scale=6):
                        with gr.Row():
                            id_final_output = gr.Image(label="🪪 冲印级标准证件照", type="pil", format="png")
                            id_cutout_output = gr.Image(label="👤 透明底图 (备用)", type="pil", format="png")
                        id_info_output = gr.Markdown()

                btn_run_id.click(
                    fn=service.process_id_photo,
                    inputs=[
                        id_input_img,
                        id_spec_dropdown,
                        id_color_radio,
                        id_model_dropdown,
                        id_device_radio,
                        id_feather,
                        id_denoise,
                    ],
                    outputs=[id_final_output, id_cutout_output, id_info_output],
                )

            # =========================================================
            # Tab 4: 电商商品智能工坊 (E-Commerce Studio)
            # =========================================================
            with gr.Tab("🛍️ 电商商品工坊 (E-Commerce Studio)"):
                gr.Markdown(
                    """
### 🛍️ 电商商品智能工坊 · 全自动商用级多平台出图
#### 实拍图发丝级去背 · 物理级真实投影 · 语义卖点提炼 · 淘宝/亚马逊/小红书多平台规格式排版
"""
                )
                with gr.Row():
                    # 左侧输入控制列 (5 列)
                    with gr.Column(scale=5):
                        ecom_input_image = gr.Image(
                            type="pil",
                            label="📸 上传商品原图 (支持手机随手拍/白底/杂景图)",
                        )
                        with gr.Row():
                            ecom_model = gr.Dropdown(
                                choices=model_choices,
                                value=default_model,
                                label="🧠 抠图模型",
                            )
                            ecom_device = gr.Radio(
                                choices=[(label, val) for val, label in device_choices],
                                value=default_device,
                                label="⚡ 运算设备",
                            )

                        with gr.Group():
                            gr.Markdown("#### ✍️ 产品信息与营销文案设定")
                            ecom_name = gr.Textbox(
                                label="产品名称 & 类目",
                                value="极光赋活紧致修护精华液",
                                placeholder="如: 极光赋活紧致修护精华液",
                            )
                            with gr.Row():
                                ecom_usage = gr.Textbox(
                                    label="核心功效 / 用途",
                                    value="深层补水 · 熬夜暗沉急救",
                                    placeholder="如: 深层补水、紧致淡纹",
                                )
                                ecom_audience = gr.Textbox(
                                    label="目标受众 / 客户群",
                                    value="25-35岁都市白领 / 熬夜党",
                                    placeholder="如: 职场女性、学生党、成分党",
                                )
                            ecom_tone = gr.Dropdown(
                                label="视觉风格调性",
                                choices=["极简轻奢", "清新自然", "科技机能", "活力青春", "法式优雅"],
                                value="极简轻奢",
                            )

                        with gr.Group():
                            gr.Markdown("#### 📐 目标生成平台与多规格分发")
                            ecom_platforms = gr.CheckboxGroup(
                                choices=ECOMMERCE_PLATFORMS,
                                value=["taobao_main", "amazon_main", "red_poster", "detail_banner"],
                                label="勾选需要自动生成的平台规格 (多选)",
                            )

                        with gr.Group():
                            gr.Markdown("#### 🏛️ 展台与物理阴影参数")
                            with gr.Row():
                                ecom_podium = gr.Dropdown(
                                    choices=ECOMMERCE_PODIUM_CHOICES,
                                    value="marble_cylinder",
                                    label="3D 商业展台底座",
                                )
                                ecom_shadow_slider = gr.Slider(
                                    minimum=0.0,
                                    maximum=2.0,
                                    value=1.0,
                                    step=0.1,
                                    label="物理光影强度",
                                )
                            with gr.Row():
                                ecom_feather = gr.Slider(
                                    minimum=0,
                                    maximum=5,
                                    value=1,
                                    step=1,
                                    label="边缘羽化半径",
                                )
                                ecom_defringe = gr.Checkbox(
                                    value=True,
                                    label="✨ 消除拍摄环境反光色溢 (Defringe)",
                                )

                        btn_run_ecom = gr.Button("🚀 一键全自动生成全套电商资产包", variant="primary", size="lg")

                    # 右侧成果画廊列 (7 列)
                    with gr.Column(scale=7):
                        ecom_status = gr.Markdown("💡 上传商品原图后点击左下方按钮，系统将全自动进行：主体保真去背 -> 语义策划 -> 物理阴影与展台 -> 多平台排版。")
                        
                        ecom_zip_file = gr.File(label="📦 一键打包下载全套电商图包 (.zip)")

                        with gr.Tabs():
                            with gr.Tab("淘宝/天猫 (1:1 展台主图)"):
                                ecom_preview_tb = gr.Image(label="800×800 爆款主图", type="pil")
                            with gr.Tab("亚马逊 (85% 规范白底图)"):
                                ecom_preview_amz = gr.Image(label="1000×1000 严格合规白底", type="pil")
                            with gr.Tab("小红书 (3:4 种草封面)"):
                                ecom_preview_red = gr.Image(label="900×1200 种草大片", type="pil")
                            with gr.Tab("详情页长条 (750px 卖点模块)"):
                                ecom_preview_detail = gr.Image(label="750×1000 详情页卖点条", type="pil")

                btn_run_ecom.click(
                    fn=service.process_ecommerce_suite,
                    inputs=[
                        ecom_input_image,
                        ecom_model,
                        ecom_device,
                        ecom_name,
                        ecom_usage,
                        ecom_audience,
                        ecom_tone,
                        ecom_platforms,
                        ecom_podium,
                        ecom_shadow_slider,
                        ecom_feather,
                        ecom_defringe,
                    ],
                    outputs=[
                        ecom_preview_tb,
                        ecom_preview_amz,
                        ecom_preview_red,
                        ecom_preview_detail,
                        ecom_zip_file,
                        ecom_status,
                    ],
                )

            # =========================================================
            # Tab 5: 离线模型资产与本地管理工坊 (Model Hub)
            # =========================================================
            with gr.Tab("📦 离线模型管理 (Model Hub)"):
                gr.Markdown(
                    """
### 📦 离线模型资产与本地导入中心
> **架构理念**：**极轻基准内置 (u2netp 4.5MB 开箱即用)** + **本地 models/ 离线包优先寻址** + **自有 GitHub Release + 国内高速镜像加速**。
> 彻底解决原作者删库断链、外网下载超时阻断以及应用打包臃肿三大痛点。
"""
                )
                model_status_df = gr.Dataframe(
                    headers=["模型代号", "模型名称", "预估体积", "运行推荐", "就绪状态", "本地文件路径"],
                    value=service.get_model_status_table(),
                    label="📋 本地模型就绪清单 (自动检索 models/ 目录与系统全局缓存)",
                    interactive=False,
                )

                btn_refresh_status = gr.Button("🔄 刷新本地模型就绪状态", size="sm")

                with gr.Row():
                    with gr.Column(scale=6):
                        gr.Markdown(
                            f"""
#### 📁 方案 3：离线模型资源包导入指南 (100% 离线免联网)
1. **项目专属模型目录**：
   `{service.get_local_models_path_str()}`
2. **极简导入方式**：
   - 从 GitHub Releases 附件或百度/夸克网盘下载预打包的 `models_pack.zip`；
   - 将需要的 `.onnx` 模型文件（如 `bria-rmbg.onnx`, `birefnet-portrait.onnx`）直接解压扔进上述 `models/` 目录；
   - 点击上方 **“🔄 刷新本地模型就绪状态”**，系统瞬间识别，永久离线免网络使用！
"""
                        )
                    with gr.Column(scale=6):
                        gr.Markdown("#### ⚡ 在线高速预下载 (自有 Release 源 + 国内镜像加速)")
                        with gr.Group():
                            dl_model_select = gr.Dropdown(
                                choices=AutoMattingEngine.supported_models(),
                                value="birefnet-portrait",
                                label="选择需要预下载的模型",
                            )
                            dl_mirror_chk = gr.Checkbox(
                                value=True,
                                label="🚀 启用国内高速镜像加速 (强烈建议开启，免代理跑满百兆宽带)",
                            )
                            btn_start_download = gr.Button("⬇️ 立即开始高速下载至 models/", variant="primary")
                            dl_result_markdown = gr.Markdown()

                # 事件绑定: 刷新表格与下载模型
                btn_refresh_status.click(
                    fn=service.get_model_status_table,
                    outputs=[model_status_df],
                )
                btn_start_download.click(
                    fn=service.download_model_ui,
                    inputs=[dl_model_select, dl_mirror_chk],
                    outputs=[dl_result_markdown],
                ).then(
                    fn=service.get_model_status_table,
                    outputs=[model_status_df],
                )

            # =========================================================
            # Tab 5: 离线模型库说明与系统架构
            # =========================================================
            with gr.Tab("📖 模型库与架构说明 (Model Guide)"):
                gr.Markdown(

                    """
### 🧠 内置支持的前沿 SOTA 离线抠图模型全景

| 模型代号 | 架构与来源 | 推荐适用场景 | 优势特征 |
| :--- | :--- | :--- | :--- |
| **`bria-rmbg`** *(默认推荐)* | Bria AI RMBG-1.4 / 2.0 | 通用物体、电商商品、高清写真 | 综合边缘表现最均衡，色彩保持好，商业级质量 |
| **`birefnet-portrait`** | BiRefNet (高分辨率双边参考) | 人像发丝、宠物绒毛、精细毛发 | 专攻“发丝与绒毛之战”，发丝边缘半透明保留极佳 |
| **`birefnet-general`** | BiRefNet (通用显著性分割) | 复杂背景构图、高反差环境 | 对高分辨率大图主体与背景分离精度极高 |
| **`u2net`** | U-2-Net (经典平衡) | 通用物体、日常人像 | 社区生态最丰富，适应性强 |
| **`u2netp`** | U-2-Net Portable | 批量处理、笔记本/低配机型 | 仅约 4.5MB 体积，毫秒级快速推理 |
| **`silueta`** | Silueta (超紧凑型) | 移动端、极速批处理 | 仅约 43MB 体积，极低资源占用 |

---
### ⚙️ 计算硬件主动配置说明
- **💻 CPU 处理器模式 (默认)**：完全依赖 CPU 线程计算，**不占用任何显存**，适合后台运行或低负荷场景；
- **⚡ GPU 独显加速模式 (DirectML)**：利用 Windows DirectX 12 自动调度 **NVIDIA GeForce GTX 1650** 独显算力，处理速度相比 CPU 提升 **10 ~ 20 倍**；
- **用户完全自主可控**：您可以在每个工作台中随时自由切换，系统采用多设备独立会话缓存，切换零卡顿。
"""
                )

    return demo


def launch_app(server_name: str = "127.0.0.1", server_port: int = 7860, inbrowser: bool = True):
    """启动本地 WebUI"""
    app = create_app()
    app.launch(server_name=server_name, server_port=server_port, inbrowser=inbrowser)


if __name__ == "__main__":
    launch_app(inbrowser=True)
