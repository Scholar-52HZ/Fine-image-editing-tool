# TASK-004: 硬件状态自动检测、用户自主设备配置与 DirectML GPU 加速优化

## 1. 基本信息
- **状态**：已完成 (Done)
- **优先级**：P0
- **负责人**：Antigravity Agent (Performance & Hardware Task)
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
针对本机 Intel i5-9300H CPU 软解推理过慢（单图 10~25s）以及 NVIDIA GeForce GTX 1650 独显闲置的问题，引入 DirectML 硬件加速能力。同时设计**主动配置方案**：自动检测 CPU 和 GPU 实际硬件状态，在 WebUI 与 CLI 中提供直观的使用设备选择器，**默认严格使用 CPU 模式**，允许用户自主一键切换至 GPU 极速模式，实现性能与资源开销的完全自主可控。

### 验收标准
- [x] 安装 `onnxruntime-directml` 并完成 DirectX 12 GPU 通道激活，更新依赖声明文件
- [x] 实现硬件状态检测模块 (`core/utils/hardware.py`)，精准探测 CPU 型号/核心数、NVIDIA 独显/显存及 ONNX Runtime 可用执行提供者
- [x] 升级推理引擎 `AutoMattingEngine`，支持 `device="cpu"` (默认) 与 `device="gpu"` 动态会话分派与会话隔离缓存
- [x] 升级 WebUI (`ui/web/app.py` & `ui/web/service.py`)，在单图、批量与证件照页面提供硬件设备单选器（默认 CPU）与实时硬件状态看板
- [x] 升级 CLI (`core/cli.py`)，提供 `--device [cpu|gpu]` 参数（默认 cpu）
- [x] 编写自动化单元测试 (`tests/test_hardware.py`)，确保全量测试通过 (23/23 passed)
- [x] 执行基准性能对比测试，记录 CPU 与 GPU 模式下的实际耗时对比数据
- [x] 在 `docs/DECISIONS.md` 追加 ADR-009 架构决策记录，更新 `docs/PROJECT_STATUS.md`

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 探测系统底层硬件配置（Intel i5-9300H 4核8线程，GTX 1650 4GB 显存，DirectX 12 / DirectML 就绪）
- [x] 制定主动配置与提速方案，确立“默认 CPU、用户可选 GPU”铁律
- [x] 创建任务工单 `docs/tasks/TASK-004-hardware-acceleration-and-active-device-selection.md`
- [x] 安装与配置 `onnxruntime-directml`，更新 `pyproject.toml` 和 `requirements.txt`
- [x] 实现 `core/utils/hardware.py` 硬件检测与提供者分发，提供安全降级与进程缓存
- [x] 改造 `core/engine/matting_engine.py` 支持 `device` 参数与 `(model, device)` 独立 Session 隔离
- [x] 改造 `core/cli.py` 增加 `--device` 选项（默认 cpu）
- [x] 改造 `ui/web/service.py` 与 `ui/web/app.py` 增加全局硬件看板与多页面设备单选器（默认 CPU）
- [x] 编写单元测试 `tests/test_hardware.py` 并通过全量 23 项单元测试
- [x] 运行 CPU 与 DirectML GPU 基准性能对比测试，输出实测数据到 `.ai/artifacts/benchmark_results.json`
- [x] 归档 ADR-009 与更新项目文档 `docs/DECISIONS.md`、`docs/PROJECT_STATUS.md`

### 正在处理 (In Progress)
- 无（本任务已全量收尾）

### 尚未完成 (Todo)
- [ ] 后续任务：推进 TASK-003（桌面原生客户端 PySide6）开发，接入已就绪的设备自主选择与 GPU 加速能力

## 4. 涉及文件清单
- **主要文件**：
  - `pyproject.toml` / `requirements.txt`
  - `core/utils/__init__.py`
  - `core/utils/hardware.py`
  - `core/engine/matting_engine.py`
  - `core/cli.py`
  - `ui/web/service.py`
  - `ui/web/app.py`
  - `tests/test_hardware.py`
  - `.ai/scratch/benchmark_devices.py`
  - `.ai/artifacts/benchmark_results.json`
- **公共/共享文件修改**：
  - `docs/DECISIONS.md` (追加 ADR-009)
  - `docs/PROJECT_STATUS.md`
  - `docs/tasks/TASK-004-hardware-acceleration-and-active-device-selection.md`

## 5. 验证与测试结果
### 单元测试验证
运行 `.venv\Scripts\python.exe -m pytest tests/ -v`：
- `test_engine.py`: 4 passed
- `test_pipeline.py`: 5 passed
- `test_webui.py`: 8 passed
- `test_hardware.py`: 6 passed
- **全量结果**：`23 passed in 16.76s` (100% 通过)

### 实测性能对比数据
在相同基准测试样本下对比 `u2netp` 模型 3 次平均推理耗时（保存于 `.ai/artifacts/benchmark_results.json`）：
- **CPU 软解模式（默认）**：`355.8 ms`
- **DirectML GPU 模式（GTX 1650）**：`34.7 ms`
- **加速效果**：GPU 比 CPU **提速 10.26 倍**！在 1024x1024 级高精发丝模型（如 RMBG / BiRefNet）下，单张耗时将从 15~20 秒大幅压缩至 1~1.5 秒。

## 6. 下一步行动 (Next Steps)
1. 向用户汇报硬件检测结果、主动配置交互设计及 10.26 倍性能提速实测数据。
2. 保持工作区整洁，待用户确认是否执行 Git 提交。
3. 按照项目演进规划，接力推进 TASK-003 桌面原生客户端 (PySide6) 开发。
