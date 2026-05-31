# Harness Builder Strategy Docs

本目录保存 Harness Builder 的产品全景规划和 POC 历史规划，用于指导后续增量功能设计。

## 文档清单

- `Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`
  - 产品全景规划。
  - 定义 Harness Builder 的长期定位、六大能力模块、Core Harness / Improvement System 分层、Experience & Self-Improve、Maturity & Evolution、目标态输出和演进路线。
  - 后续涉及产品定位、成熟度框架、智能改进、Experience、自演进、Workflow Toolkit 或长期路线图时，应优先参考。
- `Harness Builder — Agent POC计划.md`
  - 首轮 Agent POC 规划。
  - 用于回溯 POC 初始目标、验收思路和当时的 CLI / 资产范围。
  - 当前实现已经在该 POC 基础上多轮迭代，文档中的 `run` 命令和任务运行闭环内容属于历史上下文；后续实现以当前代码和工程规则为准。
- `init-north-star.md`
  - `init` 专属北极星文档。
  - 定义深度引导式 Harness 生成体验的目标态、用户旅程、CLI 视觉焦点、进度反馈、质量指标和后续迭代切片规则。
  - 后续目标模式如果围绕首次初始化、已有 Harness 维护入口、生成资产质量或 guided init 体验演进，应优先参考。

## 使用原则

1. 全景规划用于确认方向，不直接覆盖 `docs/engineering/` 中的当前工程约束。
2. POC 计划用于理解历史目标和 gap，不作为当前实现的硬约束。
3. 新增智能化、成熟度、改进候选或 Self-Improve 相关能力时，应先对照全景规划，再产出当前版本的 spec / plan。
4. 如果全景规划与当前已确认的代码边界冲突，先记录差异并在新 spec 中明确取舍。
5. 短期围绕 `init` 主体验演进时，应以 `init-north-star.md` 约束 milestone 选择，优先选择用户可感知的纵向体验切片。
