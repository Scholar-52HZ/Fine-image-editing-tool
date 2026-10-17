# TASK-XXX: [任务简要名称]

## 1. 基本信息
- **状态**：[待开始 / 进行中 / 已完成 / 挂起(Blocked)]
- **优先级**：[P0 / P1 / P2]
- **负责人**：[Agent 会话编号 / 协作分支名]
- **前置依赖 (Blocked By)**：[如无填无，或填写依赖的前序 TASK-xxx]
- **关联沙盒分支 / Worktree 目录**：`task/TASK-xxx`（若是多 Agent 并行开发模式，填写物理隔离 Worktree 路径）

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
[清晰描述本次任务要达成的用户价值与功能目标]

### 验收标准
- [ ] 验收点 1：[明确的交付功能或结果]
- [ ] 验收点 2：[异常边界与健壮性处理]
- [ ] 自动化验证与测试全量 100% Passed

## 3. 任务执行跟踪
### 已完成 (Done - 必须附物理证据链，严禁无凭据勾选)
- [x] [验收项 1] (附代码文件位置或测试日志: 如 `core/pipeline/xxx.py#L40-L65`，单测全绿) 

### 正在处理 (In Progress)
- [ ] 

### 尚未完成 (Todo)
- [ ] 

### 📸 阶段安全快照账本 (Rollback Ledger)
| 快照编号 | 阶段说明与成果 | 关联 Commit 哈希 | 一键回滚指令 |
| :--- | :--- | :--- | :--- |
| CP-1 | [阶段描述，测试全绿] | `[hash]` | `git reset --hard [hash]` |

## 4. 涉及文件清单
- **主要文件**：
  - `path/to/main/file.ext`
- **公共/共享文件修改**：
  - `path/to/shared/file.ext`
- **转正资产 (Promoted Assets)**：[若有从 .ai/ 转正的文件请在此注明，如 scripts/xxx.py 或 docs/assets/xxx.png]

## 5. 验证与测试结果
- 执行的测试或验证命令：
  ```bash
  # 测试命令记录
  ```
- 结果与结论：
  - [通过 / 异常修复记录 / 耗时与回归指标]

## 6. 下一步行动 (Next Steps)
1. [明确具体的下一步动作，方便下一个 Agent 直接开机接手]
2. [如：启动下一个任务 TASK-YYY]
