---
name: search-fix
description: When you've failed to fix the same code problem 3 or more times in a row, use this skill to search the web for solutions. Dispatch sub-agents to search multiple sources in parallel, then synthesize findings into actionable fixes. Triggers on repeated failures, "this isn't working", "I keep getting the same error", "nothing I try works", persistent bugs across multiple fix attempts.
---

# Search Fix - Web-Sourced Solutions When Stuck

When local debugging has failed 3+ times on the same problem, stop guessing. This skill orchestrates two sub-agents: one to search the web in parallel across multiple sources, then another to synthesize findings into ranked, actionable solutions.

**This skill is designed for the main conversation agent.** You are the orchestrator — you dispatch sub-agents using the `Agent` tool, wait for their results, then act on them. Do not try to do the research yourself; the sub-agent pattern is what makes this effective.

## When to use this skill

Use when ALL of these are true:
1. You've attempted at least 3 distinct fixes for the same bug/error
2. None fixed the problem (same error persists, or new errors keep appearing)
3. You don't have a clear next step

Skip if:
- This is attempt 1 or 2
- The fix is trivial (typo, missing import, syntax error)
- You already have a promising untried lead
- The problem is purely algorithmic with no external dependencies

## Workflow

### Step 1: Capture the problem

State clearly in your response to the user:
- **The error**: Exact error message and stack trace
- **What was tried**: The 3+ failed attempts and what happened each time
- **Environment**: Language, framework, versions, OS

### Step 2: Dispatch the research sub-agent

Use the `Agent` tool with `subagent_type: "general-purpose"` to dispatch a research sub-agent. Use this exact prompt template, filling in the bracketed sections:

```
Search the web for solutions to this coding problem. Use multiple sources in parallel.

PROBLEM:
[EXACT ERROR MESSAGE AND STACK TRACE]

CONTEXT:
- What was tried: [LIST EACH FAILED ATTEMPT AND RESULT]
- Environment: [LANGUAGE, FRAMEWORK, VERSIONS, OS]

SEARCH ALL OF THESE (in parallel if possible):
1. Search with Tavily MCP (mcp__tavily__tavily_search) for the exact error message in quotes, plus "fix", "solution", "workaround"
2. Search GitHub issues: "site:github.com [REPO OR KEYWORDS] [ERROR KEYWORDS]"
3. If the problem involves a specific library/framework, use Context7 MCP (mcp__plugin_context7_context7__query-docs) to check official docs
4. Search Stack Overflow: "site:stackoverflow.com [ERROR KEYWORDS]"

For promising results, use mcp__tavily__tavily_extract to fetch the full page content.
Prioritize results from the last 2 years unless the technology is older.
Do NOT use built-in WebSearch or WebFetch — always use Tavily MCP tools.

Return a structured report:

## Search Results

For each relevant result (up to 10), provide:
- **Title**: page title
- **URL**: full URL
- **Source type**: GitHub Issue / Stack Overflow / Official Docs / Blog / Forum
- **Relevance**: High / Medium / Low
- **Summary**: what this source says (2-3 sentences)
- **Proposed solution**: the fix or workaround mentioned
- **Caveats**: version requirements, warnings, limitations
```

Run this sub-agent and wait for it to complete before moving to Step 3.

### Step 3: Dispatch the synthesis sub-agent

Once the research report is complete, dispatch a second sub-agent using the `Agent` tool with `subagent_type: "general-purpose"`. Use this template:

```
You are a solution architect. Synthesize the research report below into ranked, actionable solutions.

RESEARCH REPORT:
[PASTE THE FULL RESEARCH REPORT FROM STEP 2]

ORIGINAL PROBLEM:
[ERROR AND CONTEXT FROM STEP 1]

INSTRUCTIONS:
1. Group similar solutions together
2. Rank by likelihood of success, weighting:
   - How closely the solution matches the exact error
   - Source authority (official docs > GitHub issues > Stack Overflow > blogs)
   - Recency
   - Whether it conflicts with what was already tried — if a solution matches something already attempted, flag it and look for details we might have missed
3. For each solution, explain WHY it should work (root cause reasoning)
4. Flag solutions with risks (data loss, breaking changes, version incompatibility)

Return this exact format:

# Solution Analysis: [PROBLEM SUMMARY]

## Root Cause
[Most likely root cause based on research consensus]

## Solutions (ranked by likelihood)

### Solution 1: [TITLE] ⭐ Recommended
- **Why this should work**: [root cause reasoning]
- **Steps**: [numbered, concrete steps]
- **Risk level**: Low / Medium / High
- **If this fails**: [what to try next]

### Solution 2: [TITLE]
...

## Sources
- [Title](URL) — what this contributed
```

### Step 4: Apply the top solution

After receiving the synthesis report:
1. Present the top-ranked solution to the user with a brief summary
2. Implement it step by step
3. Verify if it resolves the problem
4. If it fails, move to Solution 2, then 3
5. If all solutions fail, report to the user with the full research and everything tried

## Edge cases

### No search results found
- Re-search with parts of the error message instead of the whole thing
- Search for the broader problem category
- Search by library + symptom rather than error text
- If still nothing, tell the user the problem appears novel or extremely rare

### Top solution repeats a failed attempt
- Flag this explicitly
- Look for subtle differences in how the solution was applied
- Prioritize solutions that take a fundamentally different approach

### Multiple plausible root causes
- Present all with community consensus ranking
- Suggest a diagnostic step to narrow down which applies
- Do not guess — ask the user if needed

### Solution requires a version upgrade
- State this clearly with what the upgrade would break
- Look for workarounds compatible with the current version
