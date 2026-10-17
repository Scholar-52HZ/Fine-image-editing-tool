# 🎨 抠图工具 (Matting Studio)

> 本地离线、高保真发丝级智能抠图与背景替换工具。

---

## 🤖 AI 智能体协作与接手提示

本项目已全面遵循 **`/agent-handoff-workflow`** 多智能体协作规范：

- 🤖 **所有 AI 助手请优先阅读**：[AGENTS.md](file:///e:/DevelopProject/项目开发/抠图工具/AGENTS.md)
- 📌 **宏观全景与当前进度**：[docs/PROJECT_STATUS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/PROJECT_STATUS.md)
- 🏛️ **不可推翻的架构底线**：[docs/DECISIONS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/DECISIONS.md)
- 📝 **当前与历史工单跟踪**：[docs/tasks/](file:///e:/DevelopProject/项目开发/抠图工具/docs/tasks/)

---

## 📁 目录结构

```text
.
├── .ai/                               # 🤖 AI 专属资产与调试草稿 (.gitignore 排除)
│   ├── artifacts/                     # 生成图表、可视化预览、临时导出文件
│   └── scratch/                       # 一次性调试脚本、临时测试数据
├── AGENTS.md                          # 🤖 顶级 AI 协作与接手规范
├── docs/                              # 📁 规范文档核心
│   ├── PROJECT_STATUS.md              # 📌 宏观全景、系统架构与演进路线
│   ├── DECISIONS.md                   # 🏛️ 架构决策记录 (ADR)
│   └── tasks/                         # 📝 任务工单目录 (TASK-001, TASK-002...)
├── core/                              # ⚙️ 推理引擎与图像处理管线
│   ├── engine/                        # 多模型 ONNX Runtime 推理封装
│   ├── pipeline/                      # 边缘羽化、降噪修补、反光色溢净化、换底色
│   └── cli.py                         # 命令行原型工具
├── ui/                                # 🖥️ 交互界面层 (WebUI / Desktop)
│   └── web/                           # Gradio 交互界面与业务服务
├── tests/                             # 🧪 自动化单元测试套件
├── .gitignore                         # 忽略模型权重、临时输出与 .ai/ 缓存
├── pyproject.toml                     # 项目元数据与依赖配置
├── webui.py                           # 🌐 本地 WebUI 一键启动脚本
└── README.md                          # 项目说明
```

---

## 🌐 快速启动本地 WebUI

```bash
# 激活环境并启动 Web 交互界面
.venv\Scripts\python.exe webui.py
# 浏览器将自动打开: http://127.0.0.1:7860
```

---

## 🚀 快速接手指南

无论使用哪个 AI 助手开启新会话，只需对 AI 发送指令：
> “请阅读 AGENTS.md 接手当前项目，并继续推进下一步任务。”
