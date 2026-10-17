# TASK-005: 三位一体模型资产分层管理、离线包支持与自有 GitHub Release 镜像源落地

## 1. 基本信息
- **状态**：已完成 (Done)
- **优先级**：P0
- **负责人**：Antigravity Agent (Model Asset & Infrastructure Task)
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
针对“全量模型打包过大导致应用臃肿（>2.5GB）”、“首次点击抠图静默下载时间长”、“上游原作者 GitHub 源随时可能失效断链”三大行业痛点，结合用户确立的“方案 1（极轻内置）+ 方案 4（UI 可视化与预管理）+ 方案 3（独立离线包导入解耦）”复合思路，全面构建三位一体模型资产管理架构。

### 验收标准
- [x] 将 4.5MB 极轻核心基准模型 `u2netp.onnx` 内置于项目 `models/` 目录，在 `.gitignore` 中破例允许版本追踪，实现 0 毫秒下载等待开箱即用；
- [x] 开发 `core/utils/model_manager.py`，支持 `models/` -> `~/.rembg/` -> `~/.u2net/` 多级优先本地寻址；
- [x] 动态注入 `rembg` 会话解析机制，使核心抠图流程无缝优先读取本地 models 离线包；
- [x] 规划自有 GitHub Releases 托管体系（`Scholar-52HZ/Fine-image-editing-tool/releases/tag/v0.1.0-models`），内置国内高速镜像代理前缀（`ghfast.top` / `ghproxy.net`）；
- [x] 改造 WebUI (`ui/web/app.py` & `ui/web/service.py`)，下拉框增加实时就绪角标，新增专门的【📦 离线模型管理 (Model Hub)】工坊；
- [x] 核心抠图流程增加“未就绪拦截与温和指引”，彻底杜绝抠图时的意外无响应卡死；
- [x] 编写单元测试 `tests/test_model_manager.py`，全量 28 项测试 100% 通过；
- [x] 在 `docs/DECISIONS.md` 归档 ADR-010 架构决策，更新 `docs/PROJECT_STATUS.md`。

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 创建 `models/` 目录并复制内置极轻量模型 `u2netp.onnx` (4.4 MB)
- [x] 调整 `.gitignore` 规则，排除大体积权重同时保留内置 `models/u2netp.onnx`
- [x] 编写 `core/utils/model_manager.py` 资产探测与高速镜像下载模块
- [x] 挂载 `rembg` 本地优先钩子，实现离线模型包无感秒级加载
- [x] 在 `core/engine/matting_engine.py` 加入安全未就绪校验
- [x] 在 WebUI 增加【📦 离线模型管理 (Model Hub)】独立工作台，支持表格展示、离线包导入指引与一键高速下载
- [x] 下拉框动态渲染实时状态角标（如 `[✅ 已就绪 (项目内置)]` / `[⬇️ 未就绪 (需下载)]`）
- [x] 编写自动化测试 `tests/test_model_manager.py`，项目全量 28 项测试全过
- [x] 归档 ADR-010 架构决策与同步更新项目状态

### 正在处理 (In Progress)
- 无（全量完成）

### 尚未完成 (Todo)
- [ ] 用户后续在 GitHub Release 页面将大模型权重上传至 `v0.1.0-models` 标签附件

## 4. 涉及文件清单
- **核心文件**：
  - `models/u2netp.onnx`
  - `.gitignore`
  - `core/utils/model_manager.py`
  - `core/engine/matting_engine.py`
  - `ui/web/service.py`
  - `ui/web/app.py`
  - `tests/test_model_manager.py`
- **公共/共享文档**：
  - `docs/DECISIONS.md` (追加 ADR-010)
  - `docs/PROJECT_STATUS.md`
  - `docs/tasks/TASK-005-tiered-model-management-and-github-release-sync.md`

## 5. 验证与测试结果
运行全量测试套件：
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
**测试输出**：`28 passed in 17.03s` (100% 通过)。

## 6. 下一步行动 (Next Steps)
1. 向用户汇报三位一体架构实施结果与 WebUI 【模型管理】工坊上线情况；
2. 给出用户在 GitHub Releases 上传模型附件的操作指南。
