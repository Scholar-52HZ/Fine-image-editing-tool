# TASK-006: 电商商品智能工坊与商用全链路自动化工作流 (阶段一 ~ 阶段三)

## 1. 基本信息
- **状态**：已完成 (Done)
- **优先级**：P0
- **负责人**：Antigravity Agent (E-Commerce Pipeline & Studio Task)
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
基于现有高性能抠图引擎 (BiRefNet/RMBG + DirectML 34ms)，打通电商商品全自动商用视觉工作流，涵盖：
1. **阶段一：【电商主图基石】**：开发 `Auto-Framing` 画布规范几何自适应与物理级双层阴影发生器（接触阴影 + 柔光漫反射阴影 + 镜面微倒影），告别悬空贴纸感；
2. **阶段二：【商业展台与画廊】**：开发程序化 3D 商业展台库（大理石圆台、北欧原木托盘、水波纹光影），并在 WebUI 上线【🛍️ 电商商品智能工坊】专属操作台；
3. **阶段三：【智能文案与排版】**：开发轻量离线语义策划与多平台海报排版引擎，支持根据输入的产品名、功效用途、目标受众，一键批量生成天猫 1:1、亚马逊 85% 规范白底、小红书 3:4 种草图、详情页 750px 卖点长条，并支持一键打包 ZIP 导出。

### 验收标准
- [x] **阶段一**：
  - [x] 编写 `core/pipeline/shadow.py`：实现 `generate_contact_shadow`、`generate_ambient_shadow`、`generate_mirror_reflection` 与合成接口；
  - [x] 编写 `core/pipeline/framing.py`：实现主体包围盒提取、留白比例控制 (如 85%)、等比自适应缩放与定位对齐；
- [x] **阶段二**：
  - [x] 编写 `core/pipeline/podium.py`：实现高品质大理石展台、木质托盘、水波微光等高光与阴影自动对齐生成；
  - [x] 改造 `ui/web/app.py` 与 `ui/web/service.py`：上线第 4 个专属工坊【🛍️ 电商商品智能工坊】；
- [x] **阶段三**：
  - [x] 编写 `core/pipeline/copywriter.py`：实现基于产品属性与受众的商业文案裂变引擎（痛点标题、卖点标签、背书角标）；
  - [x] 编写 `core/pipeline/layout.py`：基于 PIL 纯本地渲染引擎，实现天猫 1:1、亚马逊 85%、小红书 3:4、详情页 750px 长条的自动排版拼图与 ZIP 打包；
  - [x] 编写全面的自动化测试套件 `tests/test_ecommerce.py`，全量 34 项测试 100% 通过；
  - [x] 同步更新 `docs/PROJECT_STATUS.md` 与记录架构决策 `docs/DECISIONS.md`。

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 完成电商全自动合成系统技术架构设计 (`ecommerce_workflow_proposal.md`)
- [x] 完成可视化交互原型设计与验证 (`ecommerce_studio_mockup.html`)
- [x] 阶段一：编写 `core/pipeline/shadow.py` 物理阴影发生器（接触阴影、柔光阴影、镜面反射）与 `core/pipeline/framing.py` 画布规范自适应
- [x] 阶段二：编写 `core/pipeline/podium.py` 商业展台库（大理石圆柱、北欧原木、水波纹、摄影棚几何块）并接入 WebUI Tab 4
- [x] 阶段三：编写 `core/pipeline/copywriter.py` 语义策划与 `core/pipeline/layout.py` 平台规格式自动化排版引擎
- [x] 贯通 `ui/web/service.py` 与 `ui/web/app.py`：支持一键批量生成全套电商规格并自动打包 ZIP 下载
- [x] 编写自动化测试 `tests/test_ecommerce.py`，全量 34 项测试 100% 通过 (17.80s)
- [x] 归档 ADR-012 架构决策并同步更新项目状态

### 正在处理 (In Progress)
- 无（全量交付完成）

### 尚未完成 (Todo)
- 无

## 4. 涉及文件清单
- **核心模块**：
  - `core/pipeline/shadow.py`
  - `core/pipeline/framing.py`
  - `core/pipeline/podium.py`
  - `core/pipeline/copywriter.py`
  - `core/pipeline/layout.py`
- **UI 与服务层**：
  - `ui/web/service.py`
  - `ui/web/app.py`
- **测试套件**：
  - `tests/test_ecommerce.py`
- **文档沉淀**：
  - `docs/DECISIONS.md` (ADR-012)
  - `docs/PROJECT_STATUS.md`
  - `docs/tasks/TASK-006-ecommerce-smart-studio-workflow.md`

## 5. 验证与测试结果
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
**测试输出**：`34 passed in 17.80s` (100% 通过)。
