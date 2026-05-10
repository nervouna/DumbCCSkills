---
name: product-brainstorming
description: 产品概念阶段头脑风暴。通过启发式对话发散功能点和场景，最终生成 HTML 头脑风暴报告。当用户说"头脑风暴"、"产品创意"、"发散一下"、"brainstorm"、"帮我构思一个产品"、"有个想法帮我展开"时触发。不适用于已有明确 PRD 进入开发、纯技术方案讨论、代码实现问题。
---

# Product Brainstorming · 产品头脑风暴

在产品概念阶段，通过启发式对话帮助用户发散功能点、探索场景、发现连接，最终生成一份自包含的 HTML 头脑风暴报告。

**核心哲学**: 发散阶段「Yes, and」——不抬杠、不反对、不评判可行性。可行性评估是收敛阶段的事。

## 何时使用

使用场景：
- "帮我头脑风暴一个产品" / "发散一下这个想法"
- "产品概念阶段，帮我展开" / "brainstorm this product idea"
- 有模糊的产品想法，需要系统化发散

跳过：
- 已有明确 PRD，直接进入开发
- 纯技术方案讨论（用什么框架、架构设计）
- 代码实现问题（用 search-fix）

## 对话流程

```
Phase 0: 预热  →  Phase 1: 发散 ⟲  →  Phase 2: 收敛  →  Phase 3: 报告
  (2-3 轮)         (用户喊停为止)         (1-2 轮)         (子代理生成)
```

### Phase 0: 预热

用 2-3 轮对话澄清核心概念：

1. 这个产品解决什么问题？
2. 谁会使用它？
3. 有什么已知的约束或假设？

浅层理解即可，不要深入。预热结束后：
1. 将问题定义写入 `state.problem_statement`
2. 将价值主张写入 `state.value_proposition`
3. 创建状态文件

#### 创建状态文件

```bash
mkdir -p docs/brainstorming
```

状态文件保存为 `docs/brainstorming/<product-slug>-brainstorm-state.json`。`<product-slug>` 从产品名派生（小写、英文、连字符分隔，例如「AI 面试助手」→ `ai-interview-coach`）。状态文件格式：

```json
{
  "product": "产品一句话描述",
  "created": "YYYY-MM-DD",
  "dimensions": [],
  "feature_ideas": [],
  "scenarios": [],
  "cross_connections": [],
  "problem_statement": "",
  "value_proposition": "",
  "open_questions": [],
  "mvp_scope": [],
  "validation_experiments": [],
  "diverge_count": 0
}
```

每个字段的结构：
- `dimensions[]`: `{"name": "维度名", "status": "pending|exploring|explored", "findings": ["发现"], "depth": "shallow|medium|deep"}`
- `feature_ideas[]`: `{"name": "功能名", "description": "描述", "source_dimension": "来源维度", "priority": "high|medium|low", "novelty": "high|medium|low"}`
- `scenarios[]`: `{"name": "场景名", "user_action": "用户行为", "system_behavior": "系统行为", "priority": "P0|P1|P2"}`
- `cross_connections[]`: `{"type": "pattern|contradiction|synergy", "description": "描述", "involved_dimensions": ["维度A", "维度B"]}`
- `open_questions[]`: `{"question": "问题", "category": "assumption|risk|unknown"}`
- `problem_statement`: Phase 0 结束时从对话提取的问题定义
- `value_proposition`: Phase 0 结束时从对话提取的价值主张
- `mvp_scope[]`: Phase 2 收敛确定的 MVP 功能点列表
- `validation_experiments[]`: Phase 2 收敛建议的验证实验列表
- `diverge_count`: 已执行发散轮数，每次触发模式 A 子代理时 +1

### Phase 1: 发散（主循环）

核心循环。只在用户说「可以了」「差不多了」「总结吧」「出报告」「stop」「converge」或类似表述时结束。

**每轮对话中：**

1. 从状态文件中选一个最有价值的待探索维度
2. 向用户提一个开放式问题
3. 如果用户说了触发词（「发散」「展开」「还有呢」「more」「depth」），派 1-2 个子代理做并行探索
4. 更新状态文件。向用户展示进度：「已探索 N 个维度，发现 M 个功能点，还有 K 个方向待展开」

**Yes, and 规则（强制执行）：**

- 构建用户的每一个想法，不拒绝、不说「但可行性呢」
- 回应必须延伸：「有意思，顺着这个思路...」「如果把这个做到极致...」「能不能再极端一点...」
- 发散阶段追求数量和广度。可行性是 Phase 2 的事

#### 子代理触发 — 模式 A：维度发散

当用户说触发词时，派 1-2 个 general-purpose 子代理。提示词模板：

```
你是一个产品头脑风暴助手。针对以下产品概念的一个特定维度进行发散思考。

产品概念：[产品一句话描述]
发散维度：[维度名称]
当前已有发现：[该维度已有的 findings]

任务：
1. 从以下视角拓展这个维度（选 2-3 个最相关的视角）：
   - 用户视角：谁会使用？在什么场景？有什么未被满足的需求？
   - 技术视角：有什么技术方案可以实现？有什么技术风险？
   - 商业视角：怎么赚钱？成本结构如何？市场规模？
   - 竞品视角：有没有类似产品？他们做得好/不好的地方？
   - 边缘场景：极端情况、小众用户、长尾需求

2. 产生 5-10 个具体的功能点或场景创意
3. 每个创意标注：名称、简短描述、新颖度（高/中/低）
4. 搜索竞品或类似方案时，使用 Tavily MCP 工具（mcp__tavily__tavily_search），不用内置搜索

返回格式：
## [维度名称] 发散结果
### 功能点
- **[名称]** (新颖度: X) - [描述]
### 场景
- **[场景名]** (新颖度: X) - [用户行为] → [系统行为]
### 待探索方向
- [后续可以深挖的方向]
```

#### 子代理触发 — 模式 B：跨维度连接

当 ≥3 个维度达到 `explored` 状态时，主动建议做跨维度分析。派一个子代理：

```
你是产品头脑风暴的连接分析器。找出以下已探索维度之间的交叉连接。

产品概念：[产品一句话描述]
已探索维度及发现：[粘贴所有 explored 维度的 findings]

任务：
1. 找出维度之间的关联模式（"A 维度的 X 场景需要 B 维度的 Y 功能支撑"）
2. 找出矛盾（"C 维度的盈利方式与 D 维度的用户场景冲突"）
3. 找出协同机会（"E 维度 + F 维度可以组合出一个新功能"）

返回格式：
## 交叉连接分析
### 关联模式
- ...
### 矛盾
- ...
### 协同机会
- ...
```

**不派子代理的情况：** 用户直接回答问题、补充具体想法、预热/澄清阶段。

### Phase 2: 收敛

用户喊停后触发。主代理处理状态文件：

1. 合并重复或相似的功能点
2. 按用户价值、新颖度排序；标注可行性备注（不做可行性门控）
3. 标注核心场景 vs 边缘场景
4. 识别跨维度主题和模式
5. 提炼待验证假设和开放问题
6. 建议 MVP 范围和验证实验

收敛结果写回状态文件的 `cross_connections`、`open_questions`、`mvp_scope` 和 `validation_experiments` 字段。

### Phase 3: 生成报告

1. 从 `<SKILL_ROOT>/assets/brainstorm-report.html` 拷贝模板
2. 将收敛后的状态数据填入模板中的 `{{PLACEHOLDER}}` 标记
3. 保存到 `docs/brainstorming/<product-slug>-report.html`
4. 用 `open` 命令打开浏览器预览

**模板填充说明：**

| 占位符 | 数据来源 |
|--------|----------|
| `{{PRODUCT_NAME}}` | state.product |
| `{{PRODUCT_TAGLINE}}` | 从 state 推导的一句话描述 |
| `{{DATE}}` | state.created |
| `{{DIVERGE_COUNT}}` | state.diverge_count |
| `{{FEATURE_COUNT}}` | state.feature_ideas.length |
| `{{SCENARIO_COUNT}}` | state.scenarios.length |
| `{{PROBLEM_STATEMENT}}` | state.problem_statement |
| `{{VALUE_PROPOSITION}}` | state.value_proposition |
| `{{PERSONA_CARDS}}` | 从 dimensions 的"用户视角"发现中提取，每张卡 `<div class="persona-card"><div class="persona-name">角色名</div><div class="persona-desc">简短描述</div></div>` |
| `{{SCENARIO_ROWS}}` | state.scenarios，每行 `<div class="scenario-row"><span>名</span><span>用户行为</span><span>系统行为</span><span class="tag tag-p0">P0</span></div>` |
| `{{FEATURE_GROUPS}}` | state.feature_ideas 按 source_dimension 分组，每组 `<div class="feature-group"><div class="group-name">维度名</div>` + feature items |
| `{{CROSS_PATTERNS}}` | cross_connections 中 type=pattern 的条目 |
| `{{CONTRADICTIONS}}` | cross_connections 中 type=contradiction 的条目 |
| `{{SYNERGIES}}` | cross_connections 中 type=synergy 的条目 |
| `{{OPEN_QUESTIONS}}` | state.open_questions |
| `{{MVP_SCOPE}}` | state.mvp_scope |
| `{{VALIDATION_EXPERIMENTS}}` | state.validation_experiments |
| `{{RESEARCH_QUESTIONS}}` | open_questions 中 category=unknown 的条目 |

模板使用 Mustache 风格条件块：

- `{{#HAS_XXX}}...{{/HAS_XXX}}` — 正向块：有数据时保留块内内容（去掉标记行）
- `{{^HAS_XXX}}...{{/HAS_XXX}}` — 反向块：无数据时保留块内内容（去掉标记行）
- 填充时根据数据是否存在，保留对应分支并去掉标记行，删除另一分支

例如场景地图区块：有数据时保留 `{{#HAS_SCENARIOS}}` 内的表格，删除 `{{^HAS_SCENARIOS}}` 内的空状态提示。

**生成步骤：**

```bash
cp "<SKILL_ROOT>/assets/brainstorm-report.html" "docs/brainstorming/<product-slug>-report.html"
# 用 Write 工具填充 HTML 文件中的占位符
open "docs/brainstorming/<product-slug>-report.html"
```

告知用户：`HTML 报告已保存到 docs/brainstorming/<product-slug>-report.html`

## 边界情况

| 情况 | 处理方式 |
|------|----------|
| 产品想法太宽泛（"一个社交网络"）| 引导分解：先窄化到特定角度或用户细分 |
| 用户一直不喊停 | 约 30 轮后温和提醒：「已经探索了不少维度，要进入收敛阶段吗？」 |
| 子代理返回结果薄弱 | 标记维度为 `shallow`，提议换个角度重新探索 |
| 状态文件损坏 | 从对话上下文重建 |
| 用户中途改变方向 | 新建维度，不覆盖。在状态文件中记录 pivot |
| 重复的想法 | 添加前检查 feature_ideas，相似则合并并注明"多次提及" |
| 非中文用户 | 所有提示词匹配用户语言，状态文件 key 保持英文，报告标题匹配用户语言 |
| 并发 session 冲突 | 报告文件名包含时间戳：`<product-slug>-report-20260511-1530.html` |
| 产品名包含特殊字符 | slug 化时移除特殊字符，只保留字母数字和连字符 |

## 核心原则

1. **先发散，后评判** — 探索阶段「Yes, and」。可行性评估是收敛阶段的事
2. **深度优先于广度** — 把一个有潜力的方向挖透，再转向下一个。一个深度洞察胜过十个浅层想法
3. **构建而非否定** — 每个用户想法都要延伸，绝不驳回
4. **状态文件是唯一真相源** — 每轮对话后更新。不要依赖记忆
5. **不是 PRD** — 这个 skill 产出头脑风暴，不是规格文档。不写 user story，不写 acceptance criteria
6. **子代理扩展广度** — 用子代理引入主对话未覆盖的新视角
