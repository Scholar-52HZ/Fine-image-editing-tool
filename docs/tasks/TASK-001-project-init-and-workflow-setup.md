# TASK-001: 项目初始化与多智能体接力规范搭建

## 1. 基本信息
- **状态**：已完成 (Done)
- **优先级**：P0
- **负责人**：Antigravity Agent (Init Session)
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
依据 `/agent-handoff-workflow` 行业标准规范，为“抠图工具”项目初始化多智能体与多会话协作基线。将仓库文件作为项目唯一的记忆载体，确保任何后续 Agent 接入时均能实现“零摩擦识别状态、无缝接力”。

### 验收标准
- [x] 在根目录创建顶级接手规则 `AGENTS.md`，定义开机 5 步协议、并行规则与交接清单
- [x] 在 `docs/` 下建立宏观状态全景 `PROJECT_STATUS.md`，包含系统架构图、技术规划、里程碑与已交付清单
- [x] 在 `docs/` 下建立技术底线与架构决策记录 `DECISIONS.md` (ADR-001 ~ ADR-004)
- [x] 在 `docs/tasks/` 下建立标准任务工单模板 `TASK-TEMPLATE.md`
- [x] 归档本次初始化任务 `TASK-001-project-init-and-workflow-setup.md` 并指明下一个任务对接点
- [x] 配置专业 `.gitignore`，隔离大模型权重文件、测试图像输出与本地环境缓存

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 梳理项目目标（发丝级/高保真本地离线抠图工具）
- [x] 设计系统拓扑图与分层架构（UI 交互层、业务服务层、推理核心层、本地存储层）
- [x] 生成 `AGENTS.md`
- [x] 生成 `docs/PROJECT_STATUS.md`
- [x] 生成 `docs/DECISIONS.md`
- [x] 生成 `docs/tasks/TASK-TEMPLATE.md`
- [x] 生成 `.gitignore`
- [x] 归档 `docs/tasks/TASK-001-project-init-and-workflow-setup.md`

### 正在处理 (In Progress)
- [ ] 无

### 尚未完成 (Todo)
- [ ] 待下任 Agent 接手并启动 TASK-002

## 4. 涉及文件清单
- **主要文件**：
  - `AGENTS.md`
  - `docs/PROJECT_STATUS.md`
  - `docs/DECISIONS.md`
  - `docs/tasks/TASK-TEMPLATE.md`
  - `docs/tasks/TASK-001-project-init-and-workflow-setup.md`
  - `.gitignore`
  - `README.md`
- **公共/共享文件修改**：
  - 无（初始化阶段创建全新框架）

## 5. 验证与测试结果
- 文件结构验证：所有核心文档已按标准路径完整落地，格式符合 Markdown 与 Mermaid 渲染标准。

## 6. 下一步行动 (Next Steps)
1. **启动 TASK-002**：技术栈选型与核心推理原型搭建（确定编程语言如 Python 3.10+、推理框架 ONNX Runtime、候选抠图模型权重如下载测试 RMBG-1.4 或 BiRefNet）。
2. **环境依赖与 CLI 原型**：编写核心接口与原型测试脚本，验证单张图片输入并导出透明背景 RGBA PNG。
