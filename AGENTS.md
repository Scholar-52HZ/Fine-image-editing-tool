# 🤖 AI 智能体协作与接手规范 (AGENTS.md)

> 本文件是所有 AI 编码助手（如 Codex、Antigravity、Cursor、Claude Code 等）在接手本项目时的**顶级系统规范**。
> 本项目采用 **“项目文件作为唯一记忆载体 (In-Repo Context & Single Source of Truth)”** 机制。无论会话如何重置或由哪位 Agent 接手，均必须严格执行以下接手与交接流程。

---

## 🎯 1. 开始工作前 5 步核对协议 (Pre-Work Protocol)

在编写任何代码或执行修改之前，**严禁盲目行动**，必须且只能先执行以下 5 步核对：

1. **阅读宏观状态**：
   - 通读 [docs/PROJECT_STATUS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/PROJECT_STATUS.md)，掌握系统整体架构、当前演进阶段、已交付功能与技术底座。
2. **查阅架构决策 (ADR)**：
   - 细读 [docs/DECISIONS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/DECISIONS.md)，了解既有的技术契约与架构底线，严禁推翻已达成共识的架构选型。
3. **定位专属任务工单（单工单精准加载）**：
   - 仅精准打开并精读本次指派的单一 `docs/tasks/TASK-*.md`，明确本次任务的目标、验收指标、前置依赖与文件影响范围；
   - **Token 上下文预算保护**：严禁无脑通读整个 tasks 目录下的所有历史工单，避免挤占模型上下文与产生思维干扰。
4. **核对物理证据链、环境与 Git 状态**：
   - 检查运行环境基线（如 `.venv`、核心依赖库、关键硬件驱动与 GPU 可用性）；
   - 检查工作区代码，核对 Git 分支/Worktree 与实际文件状态，校验最近的 `git log -n 5`；
   - **物理证据链核验 (Chain of Physical Evidence)**：校验工单中记录的“已完成 (Done)”部分，核对其所附带的代码文件路径与测试指标是否在真实物理代码中存在，严禁盲目相信未经检验的前置勾选。
5. **从“下一步”直接无缝接力**：
   - 确认无误后，直接从任务文档中的 `## 6. 下一步行动 (Next Steps)` 继续工作，不重复已做工作，不随意推翻已有成果。

---

## 👥 2. AI 原生自适应版本流协作规则 (Adaptive Git Lifecycle)

依据任务类型与开发规模，严格遵循以下动态通道与质量门禁规范：

### 2.1 动态快慢双通道 (Dynamic Dual-Speed Lanes)
- **🚀 极速修补通道 (Fast Lane - 单文件/纯文档/微调)**：
  - 仅涉及单文件改动、文档说明修补或单一参数微调时，无需创建分支，直接在当前本地分支规范提交（如 `docs: update readme`、`chore: bump version`）；
  - 远程 push 依然必须获得用户明确同意。
- **🛡️ 标准沙盒通道 (Sandbox Lane - 功能工单 TASK-xxx / 核心重构)**：
  - 凡挂接工单开发或涉及多文件逻辑重构，自动检出 `task/TASK-xxx` 独立沙盒分支；
  - **多 Agent 并行物理隔离**：多会话同时开发不同模块时，**必须且只能使用 Git Worktree 进行物理工作目录隔离**，严禁多个 Agent 同时在同一个物理文件夹中并发写代码！
    ```bash
    git worktree add ../matting-task-007 feature/task-007-desktop-gui
    ```

### 2.2 门禁式自动化微快照 (Test-Gated Micro-Checkpoints)
- **零打扰自救机制**：在沙盒分支内，AI 拥有高频打本地快照的自由，无需频繁向用户发问打断；
- **三道前置质量门禁**：仅在以下条件全部满足时方可自动执行提交：
  1. 代码无致命语法报错与导入缺失；
  2. 暂存区无模型大权重（`.onnx`/`.bin`）、大图、虚拟环境与 `.env` 敏感文件污染；
  3. 自动化测试 100% Passed；
- **快照命名**：`checkpoint(TASK-xxx): [具体阶段进展描述]`。

### 2.3 工单内嵌快照账本与一键回滚 (In-Task Rollback Ledger)
- 每次生成 checkpoint 后，AI **必须自动在对应 `docs/tasks/TASK-xxx.md` 的【快照账本】表格中追加一条记录**（登记快照编号、阶段成果、Commit 哈希及一键回退指令）；
- 若编码走偏或写崩，用户指示“回退到 CP-x”时，AI 立即根据账本秒级精准无损复原。

### 2.4 双闸门受控交付 (Dual-Gated Promotion)
- **闸门一（主干合并审批）**：
  - 工单全部验收完成、测试全绿后，AI 自动提取工单已完成项，生成规范的 Conventional Commit 摘要向用户汇报；
  - **经用户明确同意后**，AI 执行 `git checkout main && git merge --squash task/TASK-xxx && git commit -m "feat(TASK-xxx): ..."`，将零碎快照聚合为一条工业级正式大版本提交，并清理本地沙盒分支；
- **闸门二（远程发布受权）**：
  - 合并到主干后，向用户申请推送；**经用户明确同意后**，方可执行 `git push origin main`。未获同意严禁擅自上传！

## 🛡️ 3. 项目内设计方案落盘规范 (docs/designs/) 与临时资产规范 (.ai/)

为了让不同 AI 工具（Codex、Claude、Antigravity 等）及跨会话开发能够无缝共享所有方案，同时杜绝根目录散乱污染与文件遗失在 IDE 私有目录：

1. **核心架构设计与重构方案落盘 (`docs/designs/`)**：
   - 所有重大业务方案、改版规划、工作流设计（如 `ecommerce_v3_director_workflow.md`）与原型说明，**必须 100% 物理保存在项目的 `docs/designs/`**。
   - **严禁 Brain 孤岛**：严禁仅将设计方案写在 IDE 私有脑库（如 Antigravity 的 `brain/<conversation-id>/`）而不落盘到项目内。项目文件是唯一权威真源。
2. **存放路径约定**：
   - **一次性调试脚本 / 模拟测试数据**：必须存放于项目内的 `.ai/scratch/`（例如 `.ai/scratch/test_pipeline.py`）；
   - **AI 生成的图片 / 图表 / 中间预览产物**：必须存放于项目内的 `.ai/artifacts/`（例如 `.ai/artifacts/circle_mask_preview.png`）。
3. **严禁根目录散落**：
   - 严禁任何 Agent 直接在项目根目录临时创建 `test.py`、`scratch.py`、`temp.json` 等散乱碎片文件。
4. **Git 隔离与追踪边界**：
   - `docs/designs/` 必须被 Git 追踪，作为长期核心资产；
   - 项目的 `.gitignore` 必须声明 `.ai/`，确保所有 AI 工具生成的临时草稿、日志和测试图像永不污染 Git 历史。

---

## 🏁 4. 结束工作前交接清单 (Pre-Handoff Checklist)

在向用户汇报或挂起当前任务前，当前 Agent 必须完成以下交接检查：

- [ ] **设计方案与架构原生落盘**：确认本轮对话生成的所有方案文档已 100% 物理保存在 `docs/designs/`，无残留遗留在 IDE 私有的 Brain/Artifact 缓存中。
- [ ] **清理/归档临时脚本**：临时调试产物确认已置于 `.ai/scratch/`，中间生成图置于 `.ai/artifacts/`，根目录无未追踪散乱文件。
- [ ] **代码与测试验证**：运行全套自动化测试套件，确保 100% Passed，无破坏性变更与性能劣化。
- [ ] **工单与快照账本同步 (物理证据链绑定)**：更新本次 `docs/tasks/TASK-xxx.md`，勾选已完成项时**必须附带具体代码文件路径或单测凭据**（杜绝无凭无据的伪完成）；确认阶段安全快照已如实记入【快照账本】。
- [ ] **架构决策归档**：若在开发过程中引入了新的第三方依赖、变更了关键架构设计或通信协议，必须在 [docs/DECISIONS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/DECISIONS.md) 追加 ADR 记录。
- [ ] **保持宏观状态同步**：若完成了阶段性里程碑，同步更新 [docs/PROJECT_STATUS.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/PROJECT_STATUS.md) 的已交付成果清单与 RoadMap。
- [ ] **双闸门受控交付汇报**：向用户汇报交付清单与 Commit 摘要，**经用户明确同意后**方可执行主干 Squash 聚合合并（若启用了独立 Worktree 沙盒，合并后顺手执行 `git worktree remove` 与 `git worktree prune` 清理）；**经用户明确指示后**方可推送到 GitHub 远程仓库。并在最终回复中输出清晰接续点。
