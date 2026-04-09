---
name: syn-insights
description: Query Syntropic137 observability data; sessions, artifacts, token costs, tool timelines, and system-wide insights
argument-hint: <overview|sessions|artifacts|costs|tools|tokens> [args]
model: sonnet
---

# /syn-insights: Observability

Use this skill when you need to answer two questions: **"Why was this execution expensive?"** and **"Why did this session fail?"** These are the questions observability data exists to answer.

## When to Use This

Use `/syn-insights` when you want to: browse sessions and their costs, inspect what artifacts an execution produced, trace which tools a session called and in what order, or check platform-wide cost summaries.

For the **conceptual model** behind sessions, cost projections, and the two-lane architecture, the observability skill has the full explanation. For **controlling a running execution**, use `/syn-control`.

## Sessions

A session = one Claude CLI invocation in one workspace. A 3-phase workflow creates 3 sessions.

```bash
syn insights sessions                              # all sessions
syn insights sessions --workflow <workflow-id>     # filter by workflow
syn insights sessions --status running             # filter by status
syn insights sessions <session-id>                 # session detail with operations log
```

API: `GET http://localhost:8137/api/v1/sessions` (supports `?workflow_id=<id>&status=<status>`)

## Artifacts

```bash
syn artifacts list
syn artifacts list --workflow <workflow-id>
syn artifacts show <artifact-id>
syn artifacts content <artifact-id> --raw
```

## Costs

```bash
syn insights costs                              # platform-wide summary
syn insights costs session <session-id>         # cost breakdown for one session
syn insights costs execution <execution-id>     # cost aggregated across all phases
```

The breakdown includes `cost_by_model` and `cost_by_tool`; these tell you whether opus usage or expensive tool calls (like `Bash`) drove the cost.

## Tool Call Timeline

The most useful debug view, showing every tool call in order with timing and success/failure:

```bash
syn insights tools <session-id>
syn insights tools <session-id> --limit 200
```

Look for `TOOL_BLOCKED` entries (the agent was denied a tool) and long `duration_ms` values (slow file reads, hanging bash commands).

## Token Metrics

Per-session token breakdown including cache hit/miss:

```bash
syn insights tokens <session-id>
```

Low `cache_read_tokens` relative to input volume means the agent is re-reading large files every turn, which is expensive and slow.

## Common Scenarios

**"This execution cost $12. What happened?"**
1. `syn insights costs execution <id>` to find which phase was most expensive
2. `syn insights costs session <session-id>` for the expensive phase: check `cost_by_model` and `cost_by_tool`
3. `syn insights tokens <session-id>` to check cache hit ratio

**"The workflow produced no artifacts. What did the agent do?"**
1. `syn insights sessions --workflow <id>` to find the session IDs
2. `syn insights tools <session-id>` to trace every tool call; look for errors or blocked tools

**"I want to see all sessions from the last run."**
`syn insights sessions --workflow <workflow-id>` lists all sessions in order, most recent first.

## Platform Overview

Cross-org health + cost summary: `syn insights overview`

This hits `GET /api/v1/organizations/overview` and shows total executions, costs, and system health status.

## Errors

On API errors, run `/syn-health`. For the full observability model (two-lane architecture, event pipeline, cost model), see the observability skill.
