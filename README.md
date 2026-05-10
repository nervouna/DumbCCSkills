# Claude Code Skills for Dumb Models

面向低能力模型的 Claude Code 辅助技能（Skills）开发仓库。通过结构化的技能工作流弥补模型推理能力不足，让"笨模型"也能完成复杂任务。每个技能是一个独立目录，包含 `SKILL.md` 工作流定义和 `evals/evals.json` 测试用例。

## 安装

```bash
./install.sh
```

脚本会在 `~/.claude/skills/` 下创建所有技能目录的符号链接。设置 `CLAUDE_SKILLS_HOME` 环境变量可覆盖安装路径。

## 技能列表

| 技能 | 用途 |
|------|------|
| **product-brainstorming** | 产品概念阶段头脑风暴，启发式对话发散功能点和场景，生成 HTML 报告 |
| **deep-research** | 多维度网络调研，分解问题 → 并行子代理搜索 → 合成结构化报告 |
| **search-fix** | 本地调试失败 3 次以上时，调度子代理搜索 Web 方案并合成可执行修复 |
| **python-scaffold** | Python 项目脚手架，uv + ruff + mypy + pytest，支持 CLI / Web / Lib 模板 |
| **frontend-preview** | 浏览器预览 + AI 截图分析 + 自动修复反馈循环，用于前端开发 |
| **safe-config** | 安全修改 Claude Code 配置（settings.json、CLAUDE.md、hooks、MCP） |

## 项目结构

```
skill-name/
  SKILL.md              # 技能工作流定义
  evals/
    evals.json          # 测试用例（触发 prompt + 断言）
  assets/               # 模板、字体等静态资源（可选）
  references/           # 引用文档，按需加载（可选）
  scripts/              # 可执行脚本（可选）

skill-name-workspace/   # 测试产物和 benchmark（gitignored）
  iteration-N/
    eval-M/
      with_skill/run-1/  {outputs/, timing.json, grading.json}
      without_skill/run-1/ (baseline)
    benchmark.json
```

## 开发约定

- 技能使用 `Agent` 工具调度子代理，不直接执行
- 搜索统一用 Tavily MCP（`mcp__tavily__tavily_search`），禁用内置 `WebSearch` / `WebFetch`
- 子代理类型用 `general-purpose`
- 每个技能有 `evals/evals.json`，至少 2-3 个测试用例

## 测试流程

1. 在 `<skill>/evals/evals.json` 中定义测试用例
2. 对每个 eval 并行启动 `with_skill` 和 `without_skill` 两个后台子代理
3. 代理完成时捕获 `total_tokens` 和 `duration_ms` 写入 `timing.json`
4. 运行评分脚本或派 grader 子代理，输出 `grading.json`
5. 聚合 benchmark 并启动查看器：

```bash
python <skill-creator>/scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>
python <skill-creator>/eval-viewer/generate_review.py <workspace>/iteration-N --benchmark <workspace>/iteration-N/benchmark.json
```

## 新增技能

1. 创建 `<skill-name>/SKILL.md`，使用 YAML frontmatter 定义 `name` 和 `description`
2. 创建 `<skill-name>/evals/evals.json`
3. 用 skill-creator 的迭代循环测试和改善
4. 更新此 README 的技能列表
