---
name: session-export
description: >
  Export the current Claude Code session conversation to a self-contained HTML file
  with editorial document styling. Use this skill whenever the user wants to save, export,
  share, archive, or download the current conversation, chat history, or dialogue.
  Triggers on "导出对话", "导出会话", "导出聊天记录", "保存对话", "export session",
  "export conversation", "save chat", "download conversation", "存档对话", "导出 HTML".
---

# Session Export

Export the current Claude Code session to a self-contained HTML file with editorial document styling.
The output is a single `.html` file saved to the project root directory.

## Workflow

### Step 1: Locate the session file

The current session ID is in the `CLAUDE_CODE_SESSION_ID` environment variable.
The JSONL file lives at:

```
~/.claude/projects/<cwd-with-slashes-replaced-by-dashes>/<session-id>.jsonl
```

For example, if `CLAUDE_CODE_SESSION_ID=abc123` and `$PWD=/Users/alice/projects/my-app`,
the path is `~/.claude/projects/-Users-alice-projects-my-app/abc123.jsonl`.

### Step 2: Run the script

```bash
python3 <skill-root>/scripts/export_session.py
```

The script automatically:
- Reads `CLAUDE_CODE_SESSION_ID` from the environment
- Resolves the JSONL path
- Parses the session, groups messages into conversation turns
- Generates a self-contained HTML file

### Step 3: Confirm the output

The HTML file is written to `$PWD/session-<first-8-chars-of-session-id>.html`.
After generation, open it in the browser so the user can see the result:

```bash
open session-*.html
```

If the user wants a different output path, pass it as the second argument:

```bash
python3 <skill-root>/scripts/export_session.py /path/to/output.html
```

## Output format

### Layout
- Maximum width 720px, centered, document-style flow
- User messages: small "You" label above, normal body text, no background
- Assistant messages: small "Claude" label above, normal body text
- Role differentiation via typographic labels rather than color or avatars
- Warm neutral palette, light mode only

### Collapsible sections (using `<details>/<summary>`, no JavaScript required)
- **Thinking blocks**: collapsed by default, show character count in summary
- **Tool use blocks**: collapsed by default, show tool name in monospace tag
- **Tool results**: collapsed by default, show line and character count in summary, full content preserved
- Expanded blocks: indented with left border, like document asides

### Features
- Self-contained: all CSS is inline, no external dependencies
- Light mode only (warm off-white background, editorial typography)
- Time dividers between turns separated by >1 hour
- Session metadata header (project, session ID, turn count, export timestamp)
- Code blocks with warm gray background and monospace font
- HTML-escaped content to prevent XSS

## Edge cases handled by the script

| Case | Behavior |
|------|----------|
| Empty session (no messages) | Renders empty state page |
| Corrupted JSONL lines | Skips with warning to stderr |
| Missing env var | Attempts to find most recent session, shows error if none found |
| Missing JSONL file | Prints clear error with path |
| Large sessions (>1000 entries) | Streams processing, truncates very long content |
| Binary/image content in tool results | Shows placeholder text instead of raw binary |
| Consecutive thinking blocks | Merged into single display block |
| Empty thinking blocks | Skipped entirely |
| System-injected XML in user messages | Stripped: task-notification, system-reminder, local-command-*, bash-*, command-* tags extracted as clean text |
| Background task notifications | Filtered entirely (internal system noise) |
