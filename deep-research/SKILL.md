---
name: deep-research
description: Multi-dimensional research on any topic. Use this skill whenever the user wants to research, investigate, verify a hypothesis, challenge a viewpoint, analyze facts, understand a controversy, compare options, or gather evidence on a question. Triggers on phrases like "调研", "研究一下", "帮我查查", "验证这个假设", "分析一下", "fact check", "investigate", "research", "what's the evidence for", "is it true that", "compare X vs Y", or any open-ended question that requires gathering and synthesizing information from multiple sources. Also use when the user asks "深度调研", "全面分析", or provides a topic with multiple competing claims.
---

# Deep Research - Multi-Dimensional Web Research

When the user poses a research question, decompose it into multiple dimensions, dispatch parallel sub-agents to search the web via Tavily MCP, and synthesize findings into a structured report.

**This skill is for the main conversation agent.** You are the orchestrator — you analyze the question, break it into dimensions, dispatch research sub-agents in parallel, then dispatch a synthesis sub-agent to produce the final report. Do not try to do the research yourself; the sub-agent pattern is what makes this effective.

**Critical rule — language matching**: The report and all communication must be in the same language as the user's question. If the user asks in Chinese, the dimension names, sub-agent instructions, section headers, and final report must all be in Chinese. If the user asks in English, everything is in English. Never produce an English report for a Chinese question or vice versa.

## When to use this skill

Use when the user asks:
- "调研 X", "研究一下 Y", "帮我查查 Z"
- "验证这个假设", "这个观点对吗", "有没有证据支持"
- "分析一下 X 的利弊", "X 和 Y 有什么区别"
- "fact check this claim", "what's the evidence for X"
- "is it true that...", "should I believe that..."
- Any question where a single search won't suffice and multiple perspectives are needed

Skip when:
- A single web search or fact lookup would answer the question (just use Tavily search directly)
- The question is purely opinion-based ("what's the best movie")
- The question is about code/technical implementation (use search-fix if stuck)

## Workflow

### Step 1: Confirm the research question

Restate the research question back to the user. If the question is vague, ask one clarifying question to narrow scope. If it's already specific, acknowledge it and proceed.

Example: "I'll research: **Is nuclear power the most cost-effective path to decarbonization?** I'll break this into dimensions around cost, speed of deployment, grid reliability, and alternatives. Sound right?"

### Step 2: Decompose into dimensions

Analyze the question and break it into 4-6 research dimensions. Each dimension should be a self-contained sub-question that:
- Addresses a distinct angle of the main question
- Can be researched independently
- Contributes a necessary piece to the overall answer

Display the dimensions to the user as a numbered list, then proceed immediately to Step 3 without waiting for confirmation.

When decomposing, think about:
- **Evidence**: What data, studies, or facts exist?
- **Counterarguments**: What do critics or skeptics say?
- **Context**: Historical background, trends, or comparisons
- **Stakeholders**: Who is affected and what are their perspectives?
- **Authority**: What do experts, institutions, or official sources say?
- **Mechanism**: How does it work, what's the causal chain?

### Step 3: Dispatch parallel research sub-agents

For each dimension, dispatch a research sub-agent using the `Agent` tool with `subagent_type: "general-purpose"`. Launch ALL sub-agents in a single message so they run concurrently.

Use this prompt template for each sub-agent:

```
Research this specific dimension of a broader question. Use Tavily MCP tools to search, extract, and crawl web content. Be thorough — search from multiple angles, fetch the most promising pages, and follow leads.

BROADER QUESTION:
[THE MAIN RESEARCH QUESTION]

YOUR DIMENSION:
[DIMENSION NAME]: [DIMENSION SUB-QUESTION]

INSTRUCTIONS:
1. **Language**: Write everything in [LANGUAGE OF USER'S QUESTION]. Search in [LANGUAGE] first, but also search in English if the topic has significant English-language sources.
2. Start with a broad search using mcp__tavily__tavily_search to identify key sources and perspectives
2. For the most relevant results, use mcp__tavily__tavily_extract to get full page content
3. If you find a high-quality source site, use mcp__tavily__tavily_crawl to systematically extract related pages
4. Search from multiple angles — don't settle for the first few results. Try rephrased queries, include opposing viewpoints, and look for primary sources (studies, official data, expert analysis)
5. Prioritize: primary sources > expert analysis > news reports > opinion pieces > social media
6. For any factual claim, try to find corroborating or contradicting sources

Do NOT use built-in WebSearch or WebFetch — always use Tavily MCP tools.

Return your findings in this format:

## Dimension: [DIMENSION NAME]

### Key findings
- [Finding 1 with source attribution — include URL]
- [Finding 2 with source attribution — include URL]
- ...

### Evidence quality
- Strong claims: [which findings have solid evidence, and from where]
- Weak claims: [which findings are speculative or thinly sourced]

### Competing perspectives
- [If there are disagreements among sources, summarize them here]

### Sources
- [Title](URL) — relevance and credibility notes
```

Run all dimension sub-agents and wait for ALL to complete before moving to Step 4.

### Step 4: Synthesize findings

Once all dimension reports are in, dispatch a synthesis sub-agent using the `Agent` tool with `subagent_type: "general-purpose"`. Use this template:

```
Synthesize multiple research dimension reports into a single structured analysis. The final report MUST be written in the same language as the main question.

MAIN QUESTION:
[THE MAIN RESEARCH QUESTION]

DIMENSION REPORTS:
[PASTE ALL DIMENSION REPORTS FROM STEP 3, LABELED]

INSTRUCTIONS:
1. **Language**: Write the entire report in the same language as the MAIN QUESTION. Section headers, content, analysis — everything must match the question's language.
2. Read all dimension reports and identify the most important findings across them
3. Check for cross-dimension patterns — do findings from different dimensions support or contradict each other?
4. Weigh the evidence quality — prioritize well-sourced claims over speculative ones
5. Identify gaps — what important angles weren't covered well?
6. Formulate an overall assessment that accounts for the strongest evidence from all dimensions

Return this exact format (translate section headers to match the question's language):

# [DESCRIPTIVE TITLE — in question's language]

## [Executive Summary / 执行摘要]
[3-5 sentences synthesizing the overall answer to the research question. Include confidence level based on source quality and consensus.]

## [Key Findings by Dimension / 各维度关键发现]

### [Dimension 1 Name]
[2-4 bullet points of the most important, well-sourced findings]

### [Dimension 2 Name]
[2-4 bullet points]

... (one section per dimension)

## [Cross-Cutting Analysis / 交叉分析]
[Patterns, contradictions, and connections that span multiple dimensions. 2-3 paragraphs.]

## [Evidence Assessment / 证据评估]
- **Strongest evidence / 最强证据**: [which claims are best supported, and by what types of sources]
- **Weakest evidence / 薄弱证据**: [which claims are speculative or thinly sourced]
- **Notable gaps / 显著缺失**: [what important information is missing or couldn't be found]

## [Overall Assessment / 总体评估]
[Definitive answer to the research question, weighted by evidence quality. If the evidence is mixed or inconclusive, say so explicitly. State what additional information would increase confidence.]

## [Sources / 来源]
[Aggregate all source URLs from all dimension reports, deduplicated. Format: - [Title](URL)]
```

### Step 5: Present the report

Present the synthesis report to the user in full. After the report, add a brief note:
- If any dimensions had notably weak evidence, flag it
- If the user might want to dig deeper into a specific dimension, suggest it
- Keep this post-report commentary to 2-3 sentences

### Step 5b: Generate HTML report

After presenting the markdown report, convert it into a self-contained HTML file and open it in the browser.

**You (the orchestrator) generate the HTML directly** — do NOT delegate this to a sub-agent. The synthesis sub-agent only returns markdown; the HTML conversion is your responsibility.

#### HTML template spec

The HTML document must be fully self-contained (inline `<style>`, no external JS/CSS except Google Fonts via `@import`). Follow this structure:

```html
<!DOCTYPE html>
<html lang="[LANGUAGE CODE: zh-CN or en]">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[RESEARCH QUESTION]</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- For Chinese (zh-CN): include Noto Sans SC. For English (en): use Inter only. -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>

  :root {
    --primary: #2563eb;
    --primary-light: #eff6ff;
    --bg: #ffffff;
    --bg-alt: #f8fafc;
    --text: #1e293b;
    --text-secondary: #64748b;
    --border: #e2e8f0;
    --success: #16a34a;
    --success-bg: #f0fdf4;
    --warning: #d97706;
    --warning-bg: #fffbeb;
    --danger: #dc2626;
    --danger-bg: #fef2f2;
    --radius: 8px;
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    /* For en: use 'Inter', system-ui, sans-serif. For zh-CN: add 'Noto Sans SC' before system-ui. */
    font-family: 'Inter', 'Noto Sans SC', system-ui, sans-serif;
    background: var(--bg-alt);
    color: var(--text);
    line-height: 1.7;
    padding: 2rem 1rem;
  }
  .container { max-width: 800px; margin: 0 auto; }

  /* Header */
  .report-header {
    background: linear-gradient(135deg, var(--primary), #7c3aed);
    color: white;
    padding: 2rem;
    border-radius: var(--radius);
    margin-bottom: 2rem;
  }
  .report-header h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }
  .report-meta { font-size: 0.875rem; opacity: 0.85; display: flex; gap: 1.5rem; flex-wrap: wrap; }
  .confidence-badge {
    display: inline-block;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(255,255,255,0.2);
  }

  /* Cards */
  .card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow);
  }
  .card h2 {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--primary);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-light);
  }
  .card h3 { font-size: 1.05rem; font-weight: 600; margin: 1rem 0 0.5rem; }

  /* Summary highlight */
  .summary-card {
    background: var(--primary-light);
    border-left: 4px solid var(--primary);
  }

  /* Dimension details */
  details { margin-bottom: 0.75rem; }
  details summary {
    cursor: pointer;
    font-weight: 600;
    padding: 0.75rem 1rem;
    background: var(--bg-alt);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  details summary::before { content: "▶"; font-size: 0.7rem; transition: transform 0.2s; }
  details[open] summary::before { transform: rotate(90deg); }
  details summary::-webkit-details-marker { display: none; }
  details .detail-content { padding: 1rem; border: 1px solid var(--border); border-top: 0; border-radius: 0 0 var(--radius) var(--radius); }

  /* Evidence tags */
  .tag {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  .tag-strong { background: var(--success-bg); color: var(--success); }
  .tag-weak { background: var(--warning-bg); color: var(--warning); }
  .tag-gap { background: var(--danger-bg); color: var(--danger); }

  /* Cross-analysis */
  .cross-analysis {
    border-left: 4px solid #7c3aed;
    background: #faf5ff;
    padding: 1.25rem;
    border-radius: 0 var(--radius) var(--radius) 0;
  }

  /* Sources */
  .sources ol { padding-left: 1.5rem; }
  .sources li { margin-bottom: 0.4rem; font-size: 0.9rem; }
  .sources a { color: var(--primary); text-decoration: none; }
  .sources a:hover { text-decoration: underline; }

  /* Lists */
  ul, ol { padding-left: 1.5rem; margin: 0.5rem 0; }
  li { margin-bottom: 0.35rem; }
  p { margin-bottom: 0.75rem; }
  a { color: var(--primary); }

  /* Print */
  @media print {
    body { background: white; padding: 0; }
    .report-header { background: var(--text) !important; -webkit-print-color-adjust: exact; }
    /* When generating HTML for print, set open attribute on all <details> elements */
    details[open] summary { border-bottom: 0; border-radius: var(--radius) var(--radius) 0 0; }
    .card { break-inside: avoid; }
  }
</style>
</head>
<body>
<div class="container">
  <!-- Header: research question, date, confidence badge -->
  <div class="report-header">
    <h1>[RESEARCH QUESTION]</h1>
    <div class="report-meta">
      <span>[DATE]</span>
      <span class="confidence-badge">[CONFIDENCE LEVEL]</span>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="card summary-card">
    <h2>[Section header in question's language]</h2>
    <p>[Summary text]</p>
  </div>

  <!-- Key Findings by Dimension — each as a collapsible <details> -->
  <div class="card">
    <h2>[Section header in question's language]</h2>
    <details open>
      <summary>[Dimension 1 Name]</summary>
      <div class="detail-content">
        [Findings as bullet list]
      </div>
    </details>
    <details>
      <summary>[Dimension 2 Name]</summary>
      <div class="detail-content">
        [Findings as bullet list]
      </div>
    </details>
    <!-- ... one per dimension -->
  </div>

  <!-- Cross-Cutting Analysis -->
  <div class="card">
    <h2>[Section header in question's language]</h2>
    <div class="cross-analysis">
      [Cross-analysis paragraphs]
    </div>
  </div>

  <!-- Evidence Assessment with colored tags -->
  <div class="card">
    <h2>[Section header in question's language]</h2>
    <h3><span class="tag tag-strong">[Strong evidence label]</span></h3>
    <p>[Strong evidence content]</p>
    <h3><span class="tag tag-weak">[Weak evidence label]</span></h3>
    <p>[Weak evidence content]</p>
    <h3><span class="tag tag-gap">[Gaps label]</span></h3>
    <p>[Gaps content]</p>
  </div>

  <!-- Overall Assessment -->
  <div class="card">
    <h2>[Section header in question's language]</h2>
    <p>[Assessment text]</p>
  </div>

  <!-- Sources -->
  <div class="card sources">
    <h2>[Section header in question's language]</h2>
    <ol>
      <li><a href="[URL]">[Title]</a></li>
      <!-- ... -->
    </ol>
  </div>
</div>
</body>
</html>
```

#### Generation steps

1. Take the markdown synthesis report from Step 4
2. Convert it into the HTML template above — map each markdown section to the corresponding HTML block
3. All section headers must be in the same language as the research question
4. Use the `Write` tool to save the file to `/tmp/deep-research-report.html`
5. Use the `Bash` tool to run: `open /tmp/deep-research-report.html`
6. Tell the user: "HTML report saved to `/tmp/deep-research-report.html`"

> **Note on concurrent runs**: If multiple deep-research sessions run simultaneously, use a timestamped filename like `/tmp/deep-research-report-20260427-1530.html` to avoid clobbering.

## Edge cases

### Too many dimensions
If the question naturally decomposes into more than 6 dimensions, prioritize the 6 most impactful ones. Mention deprioritized dimensions so the user can request them if desired.

### Very narrow question
If the question is narrow enough that 4 dimensions feel forced, use 3. Never go below 3. If 3 still feels forced, the question may not need this skill — use direct Tavily search instead.

### Conflicting findings
When sources disagree sharply, the synthesis should surface the disagreement clearly rather than picking a side. Present the evidence for each position and let the reader judge. Flag which side has stronger sourcing.

### No good sources found
If a dimension sub-agent returns thin results, the synthesis should flag it under "Notable gaps." The orchestrator may re-dispatch that dimension with different search terms.

### Non-English research
The report language MUST match the user's question language. If the question is in Chinese, write everything in Chinese: dimension names, sub-agent prompts, section headers, report content. Search in the question's language first, then supplement with English sources if the topic has significant English-language content (e.g., academic research, Western news). For Chinese questions: search 中文 sources first, then add English sources for completeness.

### Time-sensitive topics
If the question is about a recent event or fast-moving topic, instruct sub-agents to use `time_range: "week"` or `time_range: "month"` in tavily_search calls, and to prioritize recency in source selection.

### Controversial topics
For politically or socially charged topics, ensure at least one dimension explicitly searches for opposing or critical perspectives. The synthesis should present all sides fairly.
