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

All Claude Code official docs are in English. **Steps 1-3 are mandatory — do NOT skip to Tavily.** The index covers every configuration topic. Bash (`curl`, `grep`) is always available.

#### Step 1: Download the documentation index

```bash
curl -sL -o /tmp/claude-code-docs.txt https://code.claude.com/docs/llms.txt
```

This is the official Claude Code doc index designed for LLM consumption (138 lines, `- [Title](URL): Description` format). Every config topic is listed here.

#### Step 2: Find relevant pages with grep

Map the user's config request to grep keywords:

| Request topic | grep keywords |
|---|---|
| settings, config, model | `setting`, `model-config` |
| hooks, PreToolUse, PostToolUse | `hook` |
| keybindings, keyboard shortcuts | `keybinding`, `keyboard` |
| MCP server, MCP tool | `mcp` |
| CLAUDE.md, project memory | `claude-directory`, `memory` |
| permissions, auto mode, allowlist | `permission`, `auto-mode` |

```bash
grep -i "<keyword>" /tmp/claude-code-docs.txt
```

From matching lines, pick the 2-4 most relevant `.md` URLs.

#### Step 3: Fetch the doc pages

```bash
curl -sL "<URL>" | head -500
```

Pipe through `head` to avoid loading huge pages into context. Read the extracted content and produce a concise research report:

- **Feasibility**: Is this config change possible? (yes / yes with caveats / no)
- **Approach**: Which file(s) to modify, which keys/sections, correct syntax
- **Risks**: Any breaking changes, version requirements, or incompatibilities
- **Sources**: Direct URLs to the docs pages used

#### Fallback: Tavily MCP search

Use Tavily ONLY when the fetched pages are incomplete — the page exists but lacks the specific detail needed. Do NOT use it just because curl failed or grep returned no matches (the index covers everything; if grep finds nothing, try broader keywords).

- `mcp__tavily__tavily_search` with queries like `site:code.claude.com <topic>`
- `mcp__tavily__tavily_extract` to fetch full page content
- Do NOT use built-in `WebSearch` or `WebFetch`

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

## Implementation method
<How the change will be applied. For settings.json: "Delegate to update-config skill". For other files: "Direct Edit".>

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

## Quick reference

| Resource | URL |
|----------|-----|
| Documentation index (all pages) | `https://code.claude.com/docs/llms.txt` |
| Settings reference | `https://code.claude.com/docs/en/settings.md` |
| Hooks reference | `https://code.claude.com/docs/en/hooks.md` |
| Hooks guide | `https://code.claude.com/docs/en/hooks-guide.md` |
| Keybindings | `https://code.claude.com/docs/en/keybindings.md` |
| MCP configuration | `https://code.claude.com/docs/en/mcp.md` |
| .claude directory overview | `https://code.claude.com/docs/en/claude-directory.md` |
| Permissions | `https://code.claude.com/docs/en/permissions.md` |
| Model configuration | `https://code.claude.com/docs/en/model-config.md` |
| Debug configuration | `https://code.claude.com/docs/en/debug-your-config.md` |

Always download and grep the documentation index first — it's the authoritative and complete listing.
