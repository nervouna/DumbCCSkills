---
name: safe-config
description: |
  Safely modify Claude Code configuration (settings.json, CLAUDE.md, keybindings, hooks, MCP config, and more).
  ALWAYS use this skill when the user wants to change, update, add, remove, or configure ANY Claude Code setting or configuration file.
  Triggers on: "change settings", "configure Claude", "add a hook", "update keybindings", "set up MCP",
  "modify CLAUDE.md instructions", "change the model", "adjust permissions", "edit config", "帮我改配置",
  or any request involving ~/.claude/ or .claude/ files.
  This is a research-first workflow: official docs are consulted before any changes are made.
---

# Safe Config - Claude Code Configuration

A research-first workflow for modifying Claude Code configuration. Every configuration change goes through:
**Research → Plan → Approve → Implement**.

## Why this matters

Claude Code configuration evolves rapidly. Settings, hooks, and config fields change between versions. Guessing a config key or hook event name can silently fail or break existing setup. This skill ensures every change is verified against current official documentation before implementation.

## What counts as configuration

Any file under `~/.claude/` or `.claude/`:
- `settings.json` (user-level and project-level)
- `CLAUDE.md` (user instructions)
- `keybindings.json`
- Hook scripts and configuration
- MCP server configuration
- `settings.local.json`
- Managed settings (`/etc/claude-code/`)

## Workflow

Follow these steps in order. Do not skip or reorder.

### Phase 1: Research

**Goal**: Confirm the requested change is possible and identify the correct approach using official documentation.

Dispatch a subagent to search for documentation. Use both Tavily MCP and Context7 MCP in parallel when possible.

**IMPORTANT**: The research subagent MUST use Tavily MCP tools for all web search and page fetching:
- `mcp__tavily__tavily_search` for searching
- `mcp__tavily__tavily_extract` for fetching page content
- `mcp__tavily__tavily_crawl` for crawling sites if needed
Do NOT use built-in `WebSearch` or `WebFetch` — they are less reliable and require extra safety confirmations.

The research subagent must:
1. Search with Tavily MCP for the specific config topic with queries like:
   - `site:docs.anthropic.com Claude Code <topic>`
   - `site:code.claude.com Claude Code <topic>`
2. If the topic involves a specific feature (hooks, keybindings, MCP, permissions), search for that exact feature.
3. Use Context7 MCP with library ID `/anthropic/claude-code` for API-level documentation when applicable.
4. Return a concise report:
   - **Feasibility**: Is this config change possible? (yes / yes with caveats / no)
   - **Approach**: Which file(s) to modify, which keys/sections, correct syntax
   - **Risks**: Any breaking changes, version requirements, or incompatibilities
   - **Sources**: Direct URLs to the official docs pages used

The research subagent prompt template:
```
Research whether this Claude Code configuration change is possible and how to do it:
[USER'S CONFIG REQUEST]

Requirements:
- Use mcp__tavily__tavily_search to search site:docs.anthropic.com and site:code.claude.com
- Use mcp__tavily__tavily_extract to fetch any relevant pages for full content
- Do NOT use built-in WebSearch or WebFetch — always use Tavily MCP tools instead
- Find the CURRENT official documentation (not community blogs unless no official source exists)
- For each finding, include the exact URL
- If the feature requires a specific Claude Code version, note it
- Report confidence level: confirmed in official docs / based on community source / not found

Return a concise report with: Feasibility, Approach, Risks, Sources.
```

### Phase 2: Plan

**Goal**: Turn research findings into a concrete, reviewable modification plan.

After receiving the research report, dispatch a planning subagent that:

1. Reads the research report and extracts actionable items.
2. Reads the current state of any files to be modified.
3. Produces a modification plan in this exact format:

```markdown
# Configuration Change Plan

## Summary
<One sentence describing the change>

## Files to modify
- `<absolute-path>`: <what changes>

## Detailed changes
### File: `<path>`
<diff-style description of changes>

## Sources
- [<Doc title>](<URL>) — <what this source confirms>
```

The planning subagent must NOT implement anything. It only produces the plan.

### Phase 3: Approval

Present the plan to the user. Say:

> Here's the plan based on official documentation. Should I proceed?

Wait for explicit approval (e.g., "yes", "go ahead", "proceed", "好的", "可以") before making any changes.

If the user asks for modifications, update the plan and re-present.

### Phase 4: Implementation

After approval, implement the changes:

**For `settings.json` modifications**: Invoke the `update-config` skill. It handles settings.json schema validation and scope (user vs project) correctly.

**For all other config files** (`CLAUDE.md`, `keybindings.json`, hooks, MCP config, etc.):
1. Read the file first (if it exists) to confirm current state.
2. Use Edit to make the change.
3. Show the user what was changed.

## Edge cases

### Official docs don't cover the feature

If research finds no official documentation for the requested change:
- Clearly state this to the user
- Present any community sources found, marked as "unofficial / community source"
- Ask whether to proceed based on community sources or stop

### The change is already in place

If the current config already matches what the user wants:
- Report that it's already configured correctly
- Show the current values as confirmation
- Do not make changes

### Conflicting configuration

If the requested change conflicts with existing config:
- Highlight the conflict explicitly in the plan
- Ask the user which configuration should take priority
- Warn about precedence rules (e.g., project settings override user settings for most keys)

### Version-gated features

If a feature requires a newer Claude Code version than what's installed:
- Include the version requirement in the plan
- Suggest upgrading if the user wants the feature
- Offer alternatives compatible with the current version if available

## Quick reference: official doc URLs

| Topic | Primary source |
|-------|---------------|
| Settings reference | `https://docs.anthropic.com/en/docs/claude-code/settings` |
| Hooks | `https://code.claude.com/docs/en/hooks` |
| Setup & config files | `https://docs.anthropic.com/en/docs/claude-code/setup` |
| IDE integrations | `https://docs.anthropic.com/en/docs/claude-code/ide-integrations` |
| Plugins & marketplaces | `https://docs.anthropic.com/en/docs/claude-code/plugins` |
| Authentication | `https://docs.anthropic.com/en/docs/claude-code/iam` |

Always search for the most specific page first rather than starting from these general entry points.
