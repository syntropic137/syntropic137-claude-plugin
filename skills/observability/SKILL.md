---
name: observability
description: Query Syntropic137 agent sessions, tool timelines, token metrics, cost breakdowns, and interpret observability data; why was a session expensive, why did it fail
---

# Observability: Syntropic137

When an agent run costs more than expected, takes too long, or fails without an obvious cause, observability data is where you find the answer. **The telemetry lane and the domain lane are separate; querying one does not give you information from the other.** Knowing which to look at first saves significant time.

## When to Use This Skill

Use this when you are: investigating why a session was expensive, diagnosing an agent failure, auditing tool usage patterns, building cost visibility across workflows, or understanding what an agent actually did step by step.

Not needed for controlling a running execution; use execution-control for that. Not needed for listing sessions at a glance; use `/syn-insights` for quick access.

## Two-Lane Architecture

```
Lane 1: Domain State (Event Sourcing)      Lane 2: Telemetry (Append-Only)
─────────────────────────────────────      ──────────────────────────────────
AgentSession aggregate                     Token counts per message
  → authoritative session status           Tool traces with timestamps
  → operations log                         Timing and duration data
  → final cost totals                      Cache hit/miss breakdown

Query: GET /sessions/{id}                  Query: GET /observability/sessions/{id}/tools
       syn sessions show <id>                     syn observe tools <id>
                                                  syn observe tokens <id>
```

**Lane 1 is authoritative for status and totals.** Lane 2 is authoritative for real-time traces and granular per-message data. They agree on aggregate numbers but serve different questions.

## Sessions: What They Are

One `AgentSession` = one headless agent invocation in one workspace. That invocation is `claude -p` or `codex exec`, depending on the `agent.provider` the phase declared. A 3-phase workflow creates 3 sessions, and a single workflow can mix harnesses across its phases. Sessions are linked to their execution via `execution_id` and to their workflow via `workflow_id`.

**Telemetry depth is not equal across harnesses.** Hook events, subagent tracking, and TodoWrite are Claude-only, so a codex session's timeline is thinner by construction. A sparse timeline on a codex phase is expected, not a sign of failure.

List sessions: `syn sessions list`, optionally filtered with `--workflow <id>` or `--status running`.

Show a session: `syn sessions show <session-id>` to view the operations log, total tokens, cost, and duration.

Via API: `GET /api/v1/sessions`, `GET /api/v1/sessions?workflow_id=<id>&status=running`.

## Tool Timeline

The tool timeline answers: **what did the agent do, in what order, and how long did each step take?**

```bash
syn observe tools <session-id>
```

Each entry shows: tool name, duration_ms, success/failure, and the tool's input and output. `TOOL_BLOCKED` entries indicate tools the agent attempted but wasn't allowed to use; these are always worth investigating in failed sessions.

`tool_use_id` links STARTED and COMPLETED events for the same invocation; this is useful when a tool's output looks truncated (the STARTED event has the input, COMPLETED has the output).

## Token Metrics

The token breakdown answers: **where did the cost come from, and are we getting cache benefits?**

```bash
syn observe tokens <session-id>
```

Key fields: `total_input_tokens`, `total_output_tokens`, `cache_creation_tokens`, `cache_read_tokens`. High `cache_read_tokens` relative to `cache_creation_tokens` means the session is efficiently reusing context. Low cache hits with high input tokens means the agent is re-reading large files repeatedly; restructure prompts or reduce context loading.

## Costs

Summary across all sessions: `syn costs summary`

Per session: `syn costs session <session-id>`

Per workflow execution (all phases aggregated): `syn costs execution <workflow-id>`

The `SessionCost` projection breaks down cost by model and by tool; `cost_by_tool` shows which tools consumed the most tokens. `Bash` is typically the most expensive (long outputs), `Read` is the most-called.

Default pricing: input $0.01/1K tokens, output $0.03/1K tokens (configurable).

**A codex phase that declared no `model` comes back UNPRICED.** Codex does not report its model on the wire, so the platform has nothing to price against and records no cost rather than a wrong one. If a phase is missing from a cost breakdown, check whether its `agent.model` is set in the workflow YAML.

## Answering the Common Questions

**"Why was this session expensive?"**
1. Check `cost_by_model`: on a claude phase, was `opus` used where `sonnet` would do? On a codex phase, was the top-tier model used for shallow work?
2. Check `tokens_by_tool`: is `Bash` or `Read` dominating? Large command outputs or full file reads accumulate fast.
3. Check `cache_read_tokens`: low cache hits mean repeated context loading across turns.

**"Why did this session fail?"**
1. Check `syn sessions show <id>`: look at the operations log for the last entries before the error.
2. Check the tool timeline: look for `TOOL_BLOCKED` events or tools with `success: false`.
3. Check the execution's phase detail: the phase `error_message` often points directly to the cause.

**"What tools did the agent use most?"**
Check `tokens_by_tool` in the cost breakdown. Cross-reference with the tool timeline to see if any high-frequency tools produced redundant outputs.

## Event Pipeline (How Data Flows)

```
Agent (claude -p or codex exec, in Docker)
  claude: writes .agentic/analytics/events.jsonl → HookWatcher (file watcher)
  codex:  emits codex exec --json on stdout → CodexStreamProcessor
  both converge on the collector below
  → Collector (POST /events, port 8080)
  → TimescaleDB (observability hypertable)
  → Projections: SessionList, SessionCost, TokenMetrics, ToolTimeline
  → API → CLI / Dashboard
```

Events are deduplicated by SHA-256 `event_id`, so it is safe to replay or retry ingestion.

## Escalation Point

If session costs keep exceeding expectations after adjusting model selection, investigate whether the workflow's phase prompts are loading unnecessary context. The `tokens_by_tool` breakdown will show if `Read` is called on large files unnecessarily. Restructure prompts to target specific files rather than scanning broadly.

## Integration

Start here after an execution completes or fails. Feeds back into workflow-management when you need to redesign phases based on cost patterns. Use `/syn-insights` for interactive queries from Claude Code.
