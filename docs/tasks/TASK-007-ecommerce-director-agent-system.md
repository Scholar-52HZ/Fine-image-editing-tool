# TASK-007: 导演级多智能体协同电商视觉工厂与双轨智能体中枢 (阶段 1 ~ 阶段 4)

## 1. 基本信息
- **状态**：正在处理 (In Progress)
- **优先级**：P0
- **负责人**：Codex（2026-10-16 接手；原设计：Antigravity Agent）
- **关联 Worktree 目录**：主仓库当前目录 (`e:\DevelopProject\项目开发\抠图工具`)
- **设计文档依据**：[docs/designs/ecommerce_director_agent_system.md](file:///e:/DevelopProject/项目开发/抠图工具/docs/designs/ecommerce_director_agent_system.md)

## 2. 目标与验收标准 (Acceptance Criteria)
### 目标描述
按照“真实商品保真 × 场景自由定义 × 模板继承镜头与情绪”构建一键创作体验，内部采用轻量工作流，按需展开编辑、锁定和局部重做。基础抠图保持快捷操作，首版不建设自由节点画布。
**核心架构解耦原则**：方案 B 为默认配置入口，方案 A 通过外部本地服务接入；大型模型和伴侣运行时不随主程序捆绑。编排层不新增第三方框架，使用进程内执行器、版本化数据对象及 JSON 任务清单。复用 Pillow/OpenCV 图像能力，新版 HTML/SVG 负责排版。体积按主程序、运行库、字体/渲染、模型和外部伴侣分别实测，不承诺未经验证的完整安装包体积。详细预算见主方案第 3 节及 ADR-016。


### 分阶段验收标准

#### 阶段 1：智能体双轨网关与配置测试中心 (Agent Gateway & Dual-Track Settings)
- [ ] 定义版本化素材/事实/风格/分镜/任务契约及文本、图片、结构化结果与标准错误；不再仅以字符串返回值作为执行协议；
- [ ] 实现最小进程内执行器与 JSON 清单骨架，验证节点依赖、原子写入、状态与恢复边界；编排层新增第三方依赖为 0；
- [ ] 定义独立图像任务协议与能力诊断，选定一个真实生图服务供阶段 2 联调；
- [ ] 编写 `core/agents/base.py`：定义统一的 `BaseLLMClient` 抽象协议与连接诊断方法；
- [ ] 编写 `core/agents/ollama_client.py`：实现【方案 A：纯本地离线智能体】，直连本地 Ollama (`http://localhost:11434`)；
- [ ] 编写 `core/agents/openai_client.py`：实现【方案 B：统一云端 API 客户端】，兼容标准 OpenAI 格式，预设 DeepSeek 官方、阿里云百炼、智谱开放平台、硅基流动等模板；
- [ ] 编写 `core/agents/manager.py`：负责 A/B 切换、非敏感配置持久化与分能力诊断；密钥默认使用环境变量或会话内存，任务配置相互隔离，本地模式不自动转云端；
- [ ] 在 WebUI 新增专门的 **【🤖 AI 智能体配置与测速中心】**，支持 A/B 模式单选切换、一键连通性测试并返回延迟与状态；
- [ ] 编写单元测试 `tests/test_agents.py`，确保 A/B 双轨客户端协议严密。

#### 阶段 2：摄影导演分镜推演与多模态局部 ROI 自动切片 (Director Shot & ROI Engine)
- [ ] 编写 `core/agents/director.py`：结合场景、风格和真实素材规划可变数量的可执行分镜，引用素材 ID、裁剪区域和构图约束；缺视角不补造商品细节；
- [ ] 编写 `core/agents/inspector.py`：商品感知与智能切片器，自动根据轮廓特征截取局部工艺细节（ROI 智能裁剪）；
- [ ] 编写 `core/agents/copywriter_agent.py`：品牌文案策划 Agent，匹配模板情绪调性产出诗意标题、痛点标签与参数矩阵。
- [ ] 打通“一张真实商品图 + 一套风格 + 一张主图”：真实背景生成、本地主体合成与最小模板，一键成图且无需逐节点确认；记录调用、耗时、内存与输入来源。

#### 阶段 3：HTML5/CSS3 + SVG 矢量排版渲染管线 (Vector Staging Engine)
- [ ] 建立 `core/pipeline/templates/` 现代矢量模板系统及风格/构图清单，替换新版手写贴字；保留底层图像处理及旧版电商入口直至新版验收；
- [ ] 实现【美妆轻奢模板】（参考图一：香槟丝绸光影、思源宋体、字间距微张、金色圆形细线微标）；
- [ ] 实现【户外装备模板】（参考图二：湖光山色自然融合、4 组工艺圆角微距卡片 ❶❷❸❹、专业 CAD 双向尺寸箭头工程图与参数表）；
- [ ] 验证渲染运行时、中文字体、离线资源与实际分发体积；按主方案定义像素尺寸、资源预算和低分辨率提示后导出；
- [ ] 验证局部重做与锁定冲突：改文案不重新生图，资产/模板变化按依赖失效；参数、功效、认证及尺寸仅取自确认事实；固定样例经用户视觉评审。

#### 阶段 4：成套 A+/详情页多模块工作台整合与批量导出 (Multi-Panel Suite & Delivery)
- [ ] WebUI 升级为美图设计室级专业交互工作台：多图上传池（1~6张）、自由场景描述输入、模块自由勾选；
- [ ] 输出成套视觉连续的 A+ / 详情页长图流与全套主图包，支持一键 ZIP 打包。
- [ ] 验证取消、断点恢复、待处理队列、预算/缓存限制、锁定资产保护与套图风格一致性；正常生成不强制逐阶段人工确认。

## 3. 任务执行跟踪
### 已完成 (Done)
- [x] 完成工业级多智能体系统与双轨网关架构设计方案落盘 (`docs/designs/ecommerce_director_agent_system.md`)
- [x] 在 `docs/DECISIONS.md` 归档 ADR-014 架构决策
- [x] 2026-10-16 Codex 接手核验：设计文档与 ADR-014 实体存在；现有 34 项测试全部通过；确认阶段 1 尚无实现。
- [x] 2026-10-17 完成设计复审并落盘 `docs/designs/ecommerce_director_design_review_2026-10-17.md`：记录 P0/P1 缺口、数据契约和分阶段验收建议；未修改已批准架构。
- [x] 2026-10-17 根据用户指示修订主方案至 v3.1：一键创作、内部工作流、按需局部重做及轻量化约束；同步验收项、宏观状态与 ADR-016。仅设计完成，功能尚未实现。

### 正在处理 (In Progress)
- [ ] **阶段 1：智能体双轨网关与配置测试中心实现**

### 尚未完成 (Todo)
- [ ] 阶段 2：摄影导演分镜推演与多模态切片
- [ ] 阶段 3：HTML/SVG 矢量排版渲染管线
- [ ] 阶段 4：成套 A+/详情页工作台整合与批量导出

## 4. 涉及文件清单
- **核心模块**：
  - `core/workflow/`（规划：契约、执行器、清单存储）
  - `core/providers/`（规划：图像任务协议与选定适配器）
  - `core/agents/base.py`
  - `core/agents/ollama_client.py`
  - `core/agents/openai_client.py`
  - `core/agents/manager.py`
  - `core/agents/director.py`
  - `core/agents/inspector.py`
  - `core/pipeline/templates/`
- **UI 与服务层**：
  - `ui/web/service.py`
  - `ui/web/app.py`
- **测试套件**：
  - `tests/test_agents.py`
- **文档沉淀**：
  - `docs/designs/ecommerce_director_agent_system.md`
  - `docs/DECISIONS.md` (ADR-014/016)
  - `docs/PROJECT_STATUS.md`
  - `docs/tasks/TASK-007-ecommerce-director-agent-system.md`

## 5. 验证与接手记录

- **核验日期**：2026-10-16。
- **现有代码基线**：`core/engine/`、`core/pipeline/` 与 Gradio WebUI 存在，电商阴影、展台、排版和导出已有实现。`core/agents/`、`tests/test_agents.py` 和智能体配置面板尚不存在，阶段 1 验收项保持未完成。
- **测试命令**：`.venv\Scripts\python.exe -m pytest tests/ -q`。
- **测试结果**：`34 passed in 37.36s`。该结果验证现有功能基线，不代表已完成智能体接口联调或视觉效果验收。
- **Git 状态**：本地分支 `main` 尚无提交，`git ls-files` 为空，现有项目文件均未追踪；已配置 `origin`。本次未执行暂存、提交或推送，未核验远程分支内容。
- **资产边界**：`.gitignore` 已忽略 `.ai/`；本地 `models/u2netp.onnx` 存在（4,574,861 字节）。设计文档已物理落盘，但与其他项目文件一样，尚未纳入本地 Git 历史。
- **本轮范围**：完成接手审计和工单补全，未修改业务代码、依赖或架构契约。

## 6. 下一步行动 (Next Steps)

> 当前依据为 v3.1 主方案及 ADR-016。设计复审中的执行契约与轻量化方向已纳入主方案；真实服务商、渲染运行时及桌面端口约束仍待原型/专项决策。阶段 1 代码尚未开始。

1. 从阶段 1 的版本化数据契约、最小执行器及清单存储开始，编排层新增第三方依赖为 0；再接入 `core/agents/base.py`、A/B 语言客户端与独立图像协议，选定至少一个可实际联调的图像服务。
2. 实现 Ollama 适配器及配置管理，明确超时、错误返回、环境变量覆盖和密钥脱敏；持久化配置启用前先将含凭证的配置文件加入忽略规则。
3. 修改共享文件 `ui/web/service.py`、`ui/web/app.py` 接入配置与测速面板。本工单已声明这两处共享文件的修改范围；保留现有抠图与电商流程。
4. 新增 `tests/test_agents.py`，用模拟响应验证双轨协议、切换、配置和失败路径；真实服务联调需有可用的本地服务或用户提供的 API 配置。
5. 阶段 1 验收通过后更新本工单和宏观状态，再进入阶段 2。Git 提交与推送继续等待用户明确授权。

## 7. 本轮验证与快照记录

- 2026-10-17：仅修订设计/ADR/工单/宏观状态，未新增运行依赖或业务代码。全量测试 `.venv\Scripts\python.exe -m pytest tests/ -q`：`34 passed in 21.88s`；5 份关联文档的本地链接、代码围栏、编码、ADR 唯一性和设计预算检查通过。设计预算及真实成图质量尚未实测。
- 本轮未创建 Git 快照、提交或推送；本地 main 尚无历史提交，未将既有未追踪文件作为本轮成果提交。
