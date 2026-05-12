#!/usr/bin/env python3
"""
Export a Claude Code session JSONL to a self-contained HTML file.

Usage: python export_session.py [session-id | jsonl-path] [output-path]
  - With no args: reads CLAUDE_CODE_SESSION_ID from env, writes to $PWD
  - With session-id: auto-resolves the JSONL path
  - With jsonl-path: reads a specific JSONL file
  - output-path overrides the default output location
"""

import html as html_mod
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path


# ── Session discovery ──────────────────────────────────────────────────────

def get_session_id() -> str | None:
    """Get the current session ID from environment."""
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def get_project_mapped_name() -> str:
    """Map the current working directory to the project name in ~/.claude/projects/."""
    cwd = os.getcwd()
    return cwd.replace("/", "-")


def resolve_session_path(session_id: str) -> Path:
    """Resolve the JSONL path for a given session ID."""
    projects_dir = Path.home() / ".claude" / "projects" / get_project_mapped_name()
    return projects_dir / f"{session_id}.jsonl"


def find_recent_session() -> Path | None:
    """Try to find the most recent session JSONL by modification time."""
    projects_dir = Path.home() / ".claude" / "projects" / get_project_mapped_name()
    if not projects_dir.is_dir():
        return None
    jsonl_files = sorted(projects_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonl_files[0] if jsonl_files else None


# ── Content parsing ────────────────────────────────────────────────────────

def _get_xml_tag(text: str, tag: str) -> str:
    """Extract inner text of an XML tag. Returns '' if not found."""
    m = re.search(rf'<{tag}>(.*?)</{tag}>', text, flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def strip_system_tags(content: str) -> str:
    """Strip system-injected XML from user messages. Returns '' to skip the message."""
    if not content:
        return content

    first_tag = re.match(r'<([a-z][a-z0-9_-]+)', content)
    root = first_tag.group(1) if first_tag else ""

    # ── Blocks to skip entirely (internal system noise) ──
    if root in ("task-notification", "system-reminder",
                "local-command-caveat", "local-command-stdout",
                "persisted-output"):
        return ""

    # ── Command blocks: extract command name + args ──
    if root in ("command-name", "command-message", "command-args"):
        cmd_name = _get_xml_tag(content, "command-name")
        cmd_args = _get_xml_tag(content, "command-args")
        if cmd_name:
            return f"{cmd_name} {cmd_args}".strip()
        return ""

    # ── Bash blocks ──
    if root == "bash-input":
        return _get_xml_tag(content, "bash-input")

    if root in ("bash-stdout", "bash-stderr"):
        stdout = _get_xml_tag(content, "bash-stdout")
        stderr = _get_xml_tag(content, "bash-stderr")
        # Suppress empty output and the standard "no output" noise
        if stdout and stdout != "(Bash completed with no output)":
            return stdout
        if stderr:
            return stderr
        return ""

    # ── Clean up residual tags from mixed content ──
    for tag in ("local-command-caveat", "system-reminder"):
        content = re.sub(rf'<{tag}>.*?</{tag}>\s*', '', content, flags=re.DOTALL)

    return content.strip()


def extract_text(entry: dict) -> str:
    """Extract display text from any entry type."""
    msg = entry.get("message", {})
    content = msg.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list) and content:
        block = content[0]
        bt = block.get("type", "")
        if bt == "text":
            return block.get("text", "")
        elif bt == "thinking":
            return block.get("thinking", "")
        elif bt == "tool_use":
            name = block.get("name", "unknown")
            inp = block.get("input", {})
            try:
                inp_str = json.dumps(inp, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                inp_str = str(inp)
            return f"{name}\n{inp_str}"
        elif bt == "tool_result":
            raw = block.get("content", "")
            if isinstance(raw, list):
                # Multi-part tool result (e.g., text + image)
                parts = []
                for item in raw:
                    if isinstance(item, dict) and item.get("type") == "image":
                        parts.append("[Image result]")
                    elif isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            return str(raw) if raw else ""

    return ""


def classify_entry(entry: dict) -> dict | None:
    """
    Classify a JSONL entry for display.

    Returns a dict with: role, block_type, content, is_primary, timestamp, metadata
    Returns None if the entry should be skipped.
    """
    t = entry.get("type", "")

    # Skip internal entries
    if t in ("file-history-snapshot", "last-prompt", "permission-mode", "ai-title"):
        return None

    # Skip system entries
    if t == "system":
        return None

    msg = entry.get("message", {})
    timestamp = msg.get("timestamp", entry.get("timestamp", ""))

    if t == "attachment":
        attach = entry.get("attachment", {})
        attach_type = attach.get("type", "")

        # Skip internal attachment types
        skip_types = {
            "skill_listing", "mcp_instructions_delta", "plan_mode_exit",
            "command_permissions", "task_reminder", "queued_command",
            "hook_success", "hook_additional_context",
        }
        if attach_type in skip_types:
            return None

        filename = attach.get("filename", "")
        content_str = attach.get("content", "")
        if isinstance(content_str, (dict, list)):
            content_str = json.dumps(content_str, ensure_ascii=False, indent=2)

        return {
            "role": "attachment",
            "block_type": attach_type or "file",
            "content": content_str,
            "is_primary": False,
            "timestamp": timestamp,
            "metadata": {"filename": filename, "attach_type": attach_type},
        }

    if t == "user":
        if entry.get("isMeta"):
            return None

        content = msg.get("content", "")
        is_primary = True
        block_type = "text"

        if isinstance(content, list) and content:
            bt = content[0].get("type", "")
            if bt == "tool_result":
                is_primary = False
                block_type = "tool_result"
                text = extract_text(entry)
                is_error = content[0].get("is_error", False)
                return {
                    "role": "user",
                    "block_type": "tool_result",
                    "content": text,
                    "is_primary": False,
                    "timestamp": timestamp,
                    "metadata": {
                        "tool_use_id": content[0].get("tool_use_id", ""),
                        "is_error": is_error,
                        "content_len": len(text),
                    },
                }
            elif bt == "text":
                text = content[0].get("text", "")
                text = strip_system_tags(text)
                if not text:
                    return None
                if text.startswith("/") or not text.strip():
                    # Commands and empty messages
                    is_primary = False if not text.strip() else True
                    return {
                        "role": "user",
                        "block_type": "command" if text.startswith("/") else "text",
                        "content": text,
                        "is_primary": text.startswith("/") is False and bool(text.strip()),
                        "timestamp": timestamp,
                        "metadata": {},
                    }
        elif isinstance(content, str):
            content = strip_system_tags(content)
            if not content:
                return None
            return {
                "role": "user",
                "block_type": "text",
                "content": content,
                "is_primary": True,
                "timestamp": timestamp,
                "metadata": {},
            }

        return None

    if t == "assistant":
        content_list = msg.get("content", [])
        if not content_list:
            return None

        block = content_list[0]
        bt = block.get("type", "")

        if bt == "thinking":
            thinking_text = block.get("thinking", "")
            if not thinking_text.strip():
                return None
            return {
                "role": "assistant",
                "block_type": "thinking",
                "content": thinking_text,
                "is_primary": False,
                "timestamp": timestamp,
                "metadata": {"model": msg.get("model", "")},
            }

        elif bt == "tool_use":
            name = block.get("name", "unknown")
            inp = block.get("input", {})
            try:
                inp_str = json.dumps(inp, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                inp_str = str(inp)
            return {
                "role": "assistant",
                "block_type": "tool_use",
                "content": inp_str,
                "is_primary": False,
                "timestamp": timestamp,
                "metadata": {
                    "tool_name": name,
                    "tool_id": block.get("id", "")[:20],
                },
            }

        elif bt == "text":
            return {
                "role": "assistant",
                "block_type": "text",
                "content": block.get("text", ""),
                "is_primary": True,
                "timestamp": timestamp,
                "metadata": {"model": msg.get("model", "")},
            }

    return None


def load_entries(path: Path) -> list[dict]:
    """Parse JSONL file into classified display entries."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed JSON at line {line_num}: {e}", file=sys.stderr)
                continue
            classified = classify_entry(raw)
            if classified:
                entries.append(classified)
    return entries


# ── Turn grouping ──────────────────────────────────────────────────────────

def group_turns(entries: list[dict]) -> list[dict]:
    """
    Group flat entry list into conversation turns.

    A turn starts with a primary user message and contains all subsequent
    assistant blocks and tool results until the next primary user message.
    """
    turns = []
    current = None

    for entry in entries:
        role = entry["role"]
        is_primary = entry["is_primary"]

        if role == "user" and is_primary:
            if current and (current["user_blocks"] or current["assistant_blocks"] or current["attachments"]):
                turns.append(current)
            current = {
                "user_blocks": [entry],
                "attachments": [],
                "assistant_blocks": [],
                "timestamp": entry["timestamp"],
            }

        elif current is None:
            # Entries before first user message — attachments or preamble
            continue

        elif role == "attachment":
            current["attachments"].append(entry)

        elif role == "assistant":
            current["assistant_blocks"].append(entry)

        elif role == "user" and not is_primary:
            # tool_result — add to current turn
            current["assistant_blocks"].append(entry)

    if current and (current["user_blocks"] or current["assistant_blocks"] or current["attachments"]):
        turns.append(current)

    # Filter out empty turns
    turns = [t for t in turns if t["user_blocks"] or t["assistant_blocks"] or t["attachments"]]

    return turns


# ── HTML generation ────────────────────────────────────────────────────────

def escape(text: str) -> str:
    """HTML-escape text."""
    return html_mod.escape(text, quote=True)


def format_ts(ts_str: str) -> str:
    """Format ISO timestamp to readable form."""
    if not ts_str:
        return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return ts_str



def render_code_block(content: str) -> str:
    """Render content as a code block, detecting JSON for basic highlighting."""
    escaped = escape(content)

    # Try JSON highlighting
    try:
        parsed = json.loads(content)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        return f'<pre><code class="language-json">{escape(formatted)}</code></pre>'
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    return f"<pre><code>{escaped}</code></pre>"


def render_content(content: str, block_type: str, metadata: dict) -> str:
    """Render a content block's body as HTML."""

    if block_type == "thinking":
        return f'<div class="thinking-content">{escape(content)}</div>'

    elif block_type == "tool_use":
        tool_name = metadata.get("tool_name", "unknown")
        return render_code_block(content)

    elif block_type == "tool_result":
        return render_code_block(content)

    elif block_type == "command":
        return f'<span class="command-text">{escape(content)}</span>'

    else:
        # text or attachment
        # Render inline code blocks
        return render_message_text(content)


def _render_table(lines: list[str]) -> str:
    """Render a markdown table as an HTML table."""
    def split_cells(line: str) -> list[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    # First line is header, second is separator, rest are body
    header_cells = split_cells(lines[0])
    body_lines = lines[2:] if len(lines) > 2 and re.match(r'^[\|\s\-:]+$', lines[1]) else []

    parts = ["<table>"]
    parts.append("<thead><tr>")
    for cell in header_cells:
        parts.append(f"<th>{cell}</th>")
    parts.append("</tr></thead>")

    if body_lines:
        parts.append("<tbody>")
        for line in body_lines:
            parts.append("<tr>")
            for cell in split_cells(line):
                parts.append(f"<td>{cell}</td>")
            parts.append("</tr>")
        parts.append("</tbody>")

    parts.append("</table>")
    return "\n".join(parts)


def render_message_text(text: str) -> str:
    """Render message text with markdown formatting, code blocks, and paragraphs."""
    escaped = escape(text)

    # Handle fenced code blocks (```...```)
    def replace_fenced(m: re.Match) -> str:
        lang = m.group(1) or ""
        code = m.group(2).strip()
        escaped_code = escape(code)
        cls = f' class="language-{lang}"' if lang else ""
        return f"<pre><code{cls}>{escaped_code}</code></pre>"

    escaped = re.sub(r"```(\w*)\n(.*?)```", replace_fenced, escaped, flags=re.DOTALL)

    # Handle inline code (`...`)
    escaped = re.sub(r"`([^`]+)`", r'<code class="inline">\1</code>', escaped)

    # Bold (**text**)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    # Italic (*text*)
    escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)

    # Split into paragraphs by double newlines
    paragraphs = escaped.split("\n\n")
    result = []
    for para in paragraphs:
        if not para.strip():
            continue
        if para.strip().startswith(("<pre>", "<ul>", "<ol>", "<h")):
            result.append(para)
        elif re.match(r'^#{1,4}\s', para.strip()):
            heading_text = re.sub(r'^#{1,4}\s+', '', para.strip())
            result.append(f"<p><strong>{heading_text}</strong></p>")
        elif para.strip() == "---":
            result.append("<hr>")
        else:
            lines = para.strip().split("\n")
            # Detect markdown table: every line starts and ends with |
            if all(l.strip().startswith("|") and l.strip().endswith("|") for l in lines) and len(lines) >= 2:
                result.append(_render_table(lines))
            else:
                para_with_br = para.replace("\n", "<br>")
                result.append(f"<p>{para_with_br}</p>")

    return "\n".join(result)


def generate_html(session_id: str, turns: list[dict], output_path: str) -> str:
    """Generate the complete self-contained HTML document."""
    # Remove self-referencing session-export turns
    turns = [
        t for t in turns
        if not any(
            re.search(r'/session-export', b.get("content", ""))
            for b in t["user_blocks"]
        )
    ]

    total_blocks = sum(
        len(t["user_blocks"]) + len(t["assistant_blocks"]) + len(t["attachments"])
        for t in turns
    )
    export_ts = format_ts(datetime.now(timezone.utc).isoformat())
    project_name = Path(os.getcwd()).name

    html_parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Code Session — {escape(session_id[:8])} — {escape(project_name)}</title>
<style>
:root {{
    --bg: #fafaf8;
    --text: #1a1a18;
    --text-secondary: #6b6b68;
    --text-muted: #949490;
    --border: #e8e7e3;
    --code-bg: #f2f1ed;
    --accent: #b85c3a;
    --hover-bg: #f5f4f0;
    --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
}}

.container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 48px 24px 80px;
}}

/* ── Header ── */

.session-header {{
    margin-bottom: 48px;
    padding-bottom: 28px;
    border-bottom: 1px solid var(--border);
}}

.session-title {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 10px;
}}

.session-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
}}

.session-meta span {{
    font-size: 13px;
    color: var(--text-muted);
}}

.session-meta strong {{
    font-weight: 500;
    color: var(--text-secondary);
}}

/* ── Empty state ── */

.empty-state {{
    text-align: center;
    padding: 80px 24px;
    color: var(--text-muted);
    font-size: 15px;
}}

/* ── Time divider ── */

.time-divider {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 36px 0 28px;
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 500;
    font-feature-settings: "tnum";
}}

.time-divider::before,
.time-divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}}

/* ── Turn ── */

.turn {{
    margin-bottom: 36px;
}}

/* ── Message ── */

.message-block {{
    margin-bottom: 14px;
}}

.message-label {{
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    margin-bottom: 4px;
}}

.message-body {{
    font-size: 15px;
    line-height: 1.65;
    color: var(--text);
}}

.message-body p {{
    margin-bottom: 8px;
}}

.message-body p:last-child {{
    margin-bottom: 0;
}}

.message-body ul, .message-body ol {{
    margin: 8px 0;
    padding-left: 24px;
}}

.message-body li {{
    margin-bottom: 4px;
}}

/* ── Tables ── */

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 14px;
}}

thead th {{
    text-align: left;
    font-weight: 600;
    padding: 8px 12px;
    border-bottom: 2px solid var(--border);
    color: var(--text);
}}

tbody td {{
    padding: 6px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
    vertical-align: top;
}}

tbody tr:last-child td {{
    border-bottom: none;
}}

/* ── Inline code ── */

code.inline {{
    background: var(--code-bg);
    border-radius: 3px;
    padding: 1px 5px;
    font-family: var(--font-mono);
    font-size: 0.85em;
    color: var(--text-secondary);
}}

/* ── Code blocks ── */

pre {{
    background: var(--code-bg);
    color: var(--text);
    border-radius: 4px;
    padding: 14px 16px;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 13px;
    line-height: 1.55;
    margin: 8px 0;
}}

pre code {{
    background: none;
    padding: 0;
    font-size: inherit;
    color: inherit;
}}

/* ── Collapsible blocks ── */

details {{
    margin-bottom: 8px;
}}

details > summary {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    cursor: pointer;
    user-select: none;
    list-style: none;
    transition: color 0.15s;
}}

details > summary:hover {{
    color: var(--text-secondary);
}}

details > summary::-webkit-details-marker {{
    display: none;
}}

details > summary .summary-marker {{
    font-size: 10px;
    display: inline-block;
    transition: transform 0.15s;
    width: 12px;
    flex-shrink: 0;
}}

details[open] > summary .summary-marker {{
    transform: rotate(90deg);
}}

details > summary .summary-tag {{
    font-family: var(--font-mono);
    font-size: 11px;
    padding: 1px 6px;
    border-radius: 3px;
    background: var(--code-bg);
    color: var(--text-secondary);
}}

details > summary .summary-count {{
    margin-left: auto;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
}}

.work-group {{
    margin-bottom: 12px;
}}

.work-group > details > summary {{
    font-weight: 600;
    color: var(--text-secondary);
}}

.work-group > details > .details-body {{
    margin-top: 6px;
    padding-left: 16px;
    border-left: 2px solid var(--border);
}}

.work-group details {{
    margin-bottom: 4px;
}}

.work-group details:last-child {{
    margin-bottom: 0;
}}

.details-body {{
    margin-top: 8px;
    padding-left: 20px;
    border-left: 2px solid var(--border);
}}

/* ── Thinking content ── */

.thinking-content {{
    padding: 10px 0;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
}}

/* ── Tool blocks ── */

.tool-block {{
    margin-top: 4px;
}}

.tool-block pre {{
    margin: 0;
}}

/* ── Attachment ── */

.attachment-block {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    background: var(--code-bg);
    border-radius: 4px;
    font-size: 13px;
}}

.attachment-filename {{
    font-weight: 500;
    color: var(--text);
}}

.attachment-meta {{
    font-size: 11px;
    color: var(--text-muted);
}}

/* ── Command ── */

.command-text {{
    color: var(--text-muted);
    font-style: italic;
}}

/* ── Footer ── */

.session-footer {{
    margin-top: 56px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    font-size: 12px;
    color: var(--text-muted);
    text-align: center;
}}

/* ── Mobile ── */

@media (max-width: 640px) {{
    .container {{
        padding: 32px 16px 64px;
    }}
    .message-body {{
        font-size: 14px;
    }}
    pre {{
        font-size: 12px;
    }}
}}
</style>
</head>
<body>
<div class="container">

<div class="session-header">
    <div class="session-title">Claude Code Session</div>
    <div class="session-meta">
        <span>{escape(project_name)}</span>
        <span>Session <strong>{escape(session_id[:8])}</strong></span>
        <span><strong>{len(turns)}</strong> turns &middot; <strong>{total_blocks}</strong> blocks</span>
        <span>Exported {export_ts}</span>
    </div>
</div>
"""]

    if not turns:
        html_parts.append("""
<div class="empty-state">
    <p>No messages to display in this session.</p>
</div>
""")
    else:
        last_ts = None
        for turn in turns:
            # Time divider if >1 hour gap
            ts = turn.get("timestamp", "")
            if ts and last_ts:
                try:
                    current_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                    diff_hours = (current_dt - last_dt).total_seconds() / 3600
                    if diff_hours > 1:
                        html_parts.append(
                            f'<div class="time-divider">{escape(format_ts(ts))}</div>'
                        )
                except (ValueError, TypeError):
                    pass
            if ts:
                last_ts = ts

            html_parts.append('<div class="turn">')

            # User blocks
            for ub in turn["user_blocks"]:
                content = ub.get("content", "")
                bt = ub.get("block_type", "text")

                if bt == "command":
                    html_parts.append(
                        f'<div class="message-block">'
                        f'<div class="message-label">You</div>'
                        f'<div class="message-body"><span class="command-text">{escape(content)}</span></div>'
                        f'</div>'
                    )
                else:
                    html_parts.append(
                        f'<div class="message-block">'
                        f'<div class="message-label">You</div>'
                        f'<div class="message-body">'
                        f'{render_message_text(content)}</div>'
                        f'</div>'
                    )

            # Attachments
            for att in turn["attachments"]:
                fname = att.get("metadata", {}).get("filename", "file")
                attach_type = att.get("metadata", {}).get("attach_type", "")
                html_parts.append(
                    f'<div class="message-block">'
                    f'<div class="message-label">Attachment</div>'
                    f'<div class="attachment-block">'
                    f'<span class="attachment-filename">{escape(fname)}</span>'
                    f'<span class="attachment-meta">{escape(attach_type)}</span>'
                    f'</div></div>'
                )

            # Assistant blocks — merge consecutive same types
            merged = []
            for block in turn["assistant_blocks"]:
                bt = block["block_type"]
                if bt == "thinking" and merged and merged[-1]["block_type"] == "thinking":
                    merged[-1]["content"] += "\n" + block["content"]
                else:
                    merged.append(block)

            # Group consecutive work blocks (non-text) into parent groups
            i = 0
            while i < len(merged):
                block = merged[i]
                role = block["role"]
                bt = block["block_type"]
                content = block.get("content", "")
                metadata = block.get("metadata", {})

                if bt == "text":
                    # Standalone text message — always visible
                    if content.strip():
                        html_parts.append(
                            f'<div class="message-block">'
                            f'<div class="message-label">Claude</div>'
                            f'<div class="message-body">'
                            f'{render_message_text(content)}</div>'
                            f'</div>'
                        )
                    i += 1
                else:
                    # Collect consecutive work blocks into a group
                    group = []
                    while i < len(merged) and merged[i]["block_type"] != "text":
                        group.append(merged[i])
                        i += 1

                    # Render helper for a single work block
                    def render_work_block(gb):
                        gb_bt = gb["block_type"]
                        gb_content = gb.get("content", "")
                        gb_meta = gb.get("metadata", {})
                        if gb_bt == "tool_result":
                            content_len = gb_meta.get("content_len", len(gb_content))
                            line_count = gb_content.count("\n") + 1 if gb_content else 0
                            summary_text = f"Tool Result ({line_count} lines, {content_len} chars)"
                            return (
                                f'<details>'
                                f'<summary><span class="summary-marker">&#9656;</span> {escape(summary_text)}'
                                f'</summary><div class="details-body"><div class="tool-block">'
                                f'{render_content(gb_content, gb_bt, gb_meta)}'
                                f'</div></div></details>'
                            )
                        elif gb_bt == "thinking":
                            char_count = len(gb_content)
                            return (
                                f'<details>'
                                f'<summary><span class="summary-marker">&#9656;</span> Thinking'
                                f'<span class="summary-count">{char_count} chars</span>'
                                f'</summary><div class="details-body">'
                                f'{render_content(gb_content, gb_bt, gb_meta)}'
                                f'</div></details>'
                            )
                        elif gb_bt == "tool_use":
                            tool_name = gb_meta.get("tool_name", "unknown")
                            return (
                                f'<details>'
                                f'<summary><span class="summary-marker">&#9656;</span> '
                                f'<span class="summary-tag">{escape(tool_name)}</span>'
                                f'</summary><div class="details-body"><div class="tool-block">'
                                f'{render_content(gb_content, gb_bt, gb_meta)}'
                                f'</div></div></details>'
                            )
                        return ""

                    if len(group) == 1:
                        # Single block: no outer wrapper
                        html_parts.append(render_work_block(group[0]))
                    else:
                        # Multiple blocks: wrap in a parent collapsible group
                        thinking_count = sum(1 for b in group if b["block_type"] == "thinking")
                        tool_count = sum(1 for b in group if b["block_type"] in ("tool_use", "tool_result"))
                        think_chars = sum(len(b.get("content", "")) for b in group if b["block_type"] == "thinking")
                        summary_parts = []
                        if thinking_count:
                            summary_parts.append(f"{thinking_count} thinking")
                        if tool_count:
                            summary_parts.append(f"{tool_count} tools")
                        if think_chars:
                            summary_parts.append(f"{think_chars} chars")

                        html_parts.append(
                            f'<div class="work-group">'
                            f'<details>'
                            f'<summary><span class="summary-marker">&#9656;</span> '
                            f'{", ".join(summary_parts)}</summary>'
                            f'<div class="details-body">'
                        )
                        for gb in group:
                            html_parts.append(render_work_block(gb))
                        html_parts.append('</div></details></div>')

            html_parts.append("</div>")  # .turn

    # Footer
    html_parts.append(f"""
<div class="session-footer">
    {escape(project_name)} &middot; Session {escape(session_id[:8])}
</div>
</div>
</body>
</html>""")

    return "\n".join(html_parts)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    session_id = get_session_id()
    output_path = None
    jsonl_path = None

    # Parse arguments
    args = sys.argv[1:]

    if len(args) >= 1:
        arg1 = args[0]
        # Check if it looks like a path (contains / or .jsonl)
        if "/" in arg1 or arg1.endswith(".jsonl") or arg1.endswith(".json"):
            jsonl_path = Path(arg1)
        elif len(arg1) == 36 and "-" in arg1:
            # Looks like a UUID (session ID)
            session_id = arg1
        else:
            jsonl_path = Path(arg1)

    if len(args) >= 2:
        output_path = args[1]

    # Resolve JSONL path
    if jsonl_path is None:
        if session_id:
            jsonl_path = resolve_session_path(session_id)
        else:
            print("Error: CLAUDE_CODE_SESSION_ID is not set and no session ID provided.", file=sys.stderr)
            print("Usage: python export_session.py [session-id | jsonl-path] [output-path]", file=sys.stderr)

            # Try to find a recent session
            recent = find_recent_session()
            if recent:
                print(f"Hint: found recent session file: {recent}", file=sys.stderr)
            sys.exit(1)

    if not jsonl_path.exists():
        print(f"Error: session file not found at: {jsonl_path}", file=sys.stderr)
        print("Check that the session ID is correct and the session is saved to disk.", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if output_path is None:
        sid = session_id or jsonl_path.stem
        output_path = Path(os.getcwd()) / f"session-{sid[:8]}.html"
    else:
        output_path = Path(output_path)

    # Process
    print(f"Reading session from: {jsonl_path}")
    entries = load_entries(jsonl_path)
    print(f"Parsed {len(entries)} display entries")

    turns = group_turns(entries)
    print(f"Grouped into {len(turns)} turns")

    # Use file's stem as session ID if we don't have one
    display_sid = session_id or jsonl_path.stem
    html = generate_html(display_sid, turns, str(output_path))

    output_path.write_text(html, encoding="utf-8")
    print(f"Exported to: {output_path}")

    # Try to open in browser
    try:
        import subprocess
        subprocess.run(["open", str(output_path)], check=False)
        print(f"Opened in browser.")
    except Exception:
        pass


if __name__ == "__main__":
    main()
