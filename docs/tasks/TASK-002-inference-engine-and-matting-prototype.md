# TASK-002: 推理核心封装与单图/批量抠图原型实现

## 1. 基本信息
- **状态**：已完成 (Done)
- **优先级**：P0
- **负责人**：Antigravity Agent (Core Engine Task)
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
参考 GitHub 顶尖开源自动抠图方案（如 Rembg、Bria RMBG-1.4/2.0、BiRefNet、U-2-Net 等高精度发丝级离线模型），搭建基于 Python 3.11 + ONNX Runtime 的本地化核心推理引擎与图像处理管线（Core Pipeline），实现单图抠图、发丝级 Alpha 遮罩生成、自定义背景合成（透明/纯色/自定义图片）及 CLI 原型验证。

### 验收标准
- [x] 搭建 Python 3.11 本地虚拟环境并配置项目依赖（`onnxruntime`, `pillow`, `numpy`, `rembg`, `opencv-python-headless` 等）
- [x] 实现核心推理引擎接口与封装 (`core/engine/`)，支持主流 SOTA 模型（RMBG、BiRefNet、U2Net、ISNet、Silueta 等）无缝切换与本地缓存加载
- [x] 实现图像前处理与后处理管线 (`core/pipeline/`)，支持 Alpha Matting 羽化、边缘平滑去毛边、微小空洞噪点修复、边缘反光色溢净化 (Defringe) 与背景颜色/图片合成
- [x] 封装 CLI 命令行原型 (`core/cli.py`)，支持单图处理、批量处理、单独导出 Alpha 遮罩与背景更换选项
- [x] 编写全面的单元测试 (`tests/`)，验证图像输入输出、Alpha 通道有效性、纯色合成正确性及异常容错
- [x] 运行测试确保 100% 通过（9/9 passed），更新文档与交接清单

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 查阅微信公众号参考案例与 GitHub 热门方案对比分析（Rembg, BiRefNet, RMBG-2.0, U-2-Net）
- [x] 确立本地化核心架构方案：采用模块化 Engine + Pipeline 设计，底层基于 ONNX Runtime 高性能推理
- [x] 初始化 Python 3.11 虚拟环境与依赖管理 (`pyproject.toml` / `requirements.txt`)
- [x] 编写核心模块代码：`core/engine/base.py`, `core/engine/matting_engine.py`, `core/pipeline/composite.py`, `core/pipeline/refine.py`
- [x] 编写命令行工具 `core/cli.py`（单图抠图、批量处理、换底色、导出 Mask、模型列表查看）
- [x] 编写并执行单元测试 `tests/test_engine.py` 与 `tests/test_pipeline.py`
- [x] 端到端实测运行验证：合成图形样本经由 `u2netp` 模型成功完成抠图、遮罩提取与白色背景合成导出
- [x] 追加架构决策 [ADR-005](file:///e:/DevelopProject/项目开发/抠图工具/docs/DECISIONS.md#adr-005-核心推理引擎采用分层解耦与多模型统一抽象架构-engine--pipeline) 记录
- [x] 同步更新宏观状态全景 [docs/PROJECT_STATUS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/PROJECT_STATUS.md)

### 正在处理 (In Progress)
- 无

### 尚未完成 (Todo)
- 待下任 Agent 开启 TASK-003（UI 交互层界面开发）

## 4. 涉及文件清单
- **主要文件**：
  - `pyproject.toml`
  - `requirements.txt`
  - `core/__init__.py`
  - `core/engine/__init__.py`
  - `core/engine/base.py`
  - `core/engine/matting_engine.py`
  - `core/pipeline/__init__.py`
  - `core/pipeline/composite.py`
  - `core/pipeline/refine.py`
  - `core/cli.py`
  - `tests/__init__.py`
  - `tests/test_engine.py`
  - `tests/test_pipeline.py`
- **公共/共享文件修改**：
  - `docs/DECISIONS.md`（追加 ADR-005）
  - `docs/PROJECT_STATUS.md`（更新交付清单与测试命令）
  - `docs/tasks/TASK-002-inference-engine-and-matting-prototype.md`（本文档）

## 5. 验证与测试结果
- **单元测试全量通过**：
  ```text
  ============================= test session starts =============================
  platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
  rootdir: E:\DevelopProject\项目开发\抠图工具
  configfile: pyproject.toml
  collected 9 items

  tests/test_engine.py::test_supported_models PASSED                       [ 11%]
  tests/test_engine.py::test_engine_initialization_and_switching PASSED    [ 22%]
  tests/test_engine.py::test_matting_result_save_and_composite PASSED      [ 33%]
  tests/test_engine.py::test_predict_pipeline_with_mock PASSED             [ 44%]
  tests/test_pipeline.py::test_parse_color PASSED                          [ 55%]
  tests/test_pipeline.py::test_composite_with_color PASSED                 [ 66%]
  tests/test_pipeline.py::test_composite_with_image PASSED                 [ 77%]
  tests/test_pipeline.py::test_feather_mask PASSED                         [ 88%]
  tests/test_pipeline.py::test_remove_small_noise PASSED                   [100%]

  ============================== 9 passed in 3.25s ==============================
  ```
- **CLI 原型验证**：
  ```text
  .venv\Scripts\python.exe -m core.cli --list-models (模型查询成功，展示 7 款内置 SOTA 离线模型)
  .venv\Scripts\python.exe -m core.cli .ai\artifacts\sample_circle.jpg -o .ai\artifacts\sample_circle_white_bg.jpg --model u2netp --bg-color "#FFFFFF" --save-mask .ai\artifacts\sample_circle_mask.png (成功完成离线推理并导出换底图片与掩模至 .ai/artifacts/)
  ```

## 6. 下一步行动 (Next Steps)
1. **启动 TASK-003（方案 A：桌面原生客户端实现）**：基于 PySide6 构建独立桌面客户端，实现单图/多图拖拽导入、原图与抠图交互式卷帘对比、预设换底色面板及异步推理防卡死。
2. **规划 TASK-004（方案 B：本地 WebUI 实现）**：基于 Gradio / Web 框架搭建浏览器端交互界面，提供局域网免装跨设备共享。
3. **后续 TASK-005 & 006**：并发导出队列与硬件加速探测 (DirectML/CUDA)，桌面单文件免安装 EXE 打包与发布。
