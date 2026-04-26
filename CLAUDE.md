# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About

Claude Code skills development and benchmarking repo. Each skill is a project-root directory containing `SKILL.md` and `evals/evals.json`.

## Skill conventions

- Skills live in project root: `<skill-name>/SKILL.md` (not `.claude/skills/`)
- Test outputs and benchmarks go in `<skill-name>-workspace/` (gitignored via `*-workspace/`)
- Skills designed for main-agent orchestration use the `Agent` tool to dispatch sub-agents
- Web search in skills must use Tavily MCP tools, never built-in `WebSearch`/`WebFetch`

## Eval workflow

- Evals defined in `evals/evals.json` per skill
- For each eval, run `with_skill` and `without_skill` (baseline) in parallel as background sub-agents
- Grading JSON uses fields `text`, `passed`, `evidence` (not `name`/`met`/`details`)
- Aggregate with `python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>`
- Launch reviewer: `python eval-viewer/generate_review.py <workspace>/iteration-N --benchmark <workspace>/iteration-N/benchmark.json`
