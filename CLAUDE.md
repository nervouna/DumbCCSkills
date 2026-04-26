# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

Claude Code skills development and benchmarking repo. Each skill is a project-root directory containing `SKILL.md` and `evals/evals.json`.

## Skill conventions

- Skills live in project root: `<skill-name>/SKILL.md` (not `.claude/skills/`)
- Test outputs and benchmarks go in `<skill-name>-workspace/` (gitignored via `*-workspace/`)
- Skills designed for main-agent orchestration use the `Agent` tool to dispatch sub-agents
- Web search in skills must use Tavily MCP tools, never built-in `WebSearch`/`WebFetch`

## Skills

- **search-fix**: Web-sourced solutions when local debugging fails 3+ times. Dispatches research + synthesis sub-agents.
- **safe-config**: Safely modify Claude Code configuration files (settings.json, CLAUDE.md, hooks, MCP).
- **frontend-preview**: Browser preview + AI screenshot analysis + auto-fix feedback loop for frontend development.
- **deep-research**: Multi-dimensional web research on any topic. Decomposes questions into dimensions, dispatches parallel Tavily research sub-agents, and synthesizes findings into structured reports.

## Eval workflow

- Evals defined in `evals/evals.json` per skill
- For each eval, run `with_skill` and `without_skill` (baseline) in parallel as background sub-agents
- Grading JSON uses fields `text`, `passed`, `evidence` (not `name`/`met`/`details`)
- Aggregate: `python <skill-creator>/scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>`
- Review: `python <skill-creator>/eval-viewer/generate_review.py <workspace>/iteration-N --benchmark <workspace>/iteration-N/benchmark.json`

## Gotchas

- Git may fail with "not a git repository" — use `git -C /absolute/path/to/ClaudeCodeSkills` instead
- Aggregation script expects `run-1/` subdirectories inside each config; grading.json needs a `summary` field
- Skill-creator scripts live in `~/.claude/plugins/cache/claude-plugins-official/skill-creator/<hash>/skills/skill-creator/`
- Eval sub-agent prompts must NOT have "IMPORTANT: conceptual only" hints — agents will describe instead of execute
