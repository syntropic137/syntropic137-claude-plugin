---
name: observability
description: Query Syntropic137 agent sessions, tool timelines, token metrics, cost breakdowns, and interpret observability data — why was a session expensive, why did it fail
---

# Observability — Syntropic137

Use this knowledge when the user asks about sessions, costs, metrics, tool usage, token consumption, or wants to understand what an agent did during execution.

## Two-Lane Architecture

Syntropic137 separates concerns into two lanes:

- **Lane 1 (Domain State)**: Event-sourced aggregates — `AgentSession` tracks session lifecycle, operations, and status
- **Lane 2 (Telemetry)**: Append-only observations — token usage, tool traces, timing. Never replayed for state decisions.

This means there are two paths to query:
- **Session data** (Lane 1): `GET /sessions/{id}` — authoritative status, operations, final metrics
- **Telemetry data** (Lane 2): `GET /observability/sessions/{id}/tools`, `/tokens` — real-time traces

## Sessions

### What is a Session?

An `AgentSession` represents one agent execution — one Claude CLI invocation inside a workspace. A workflow execution with 3 phases creates 3 sessions (one per phase).

### Session Lifecycle

```
StartSessionCommand → SessionStartedEvent → RUNNING
  ↓
RecordOperationCommand → OperationRecordedEvent (repeated)
  ↓
CompleteSessionCommand → SessionCompletedEvent → COMPLETED | FAILED | CANCELLED
```

### Querying Sessions

```bash
# List all sessions
uv run --package syn-cli syn sessions list

# Filter by workflow
uv run --package syn-cli syn sessions list --workflow <workflow-id>

# Filter by status
uv run --package syn-cli syn sessions list --status running

# Session detail
uv run --package syn-cli syn sessions show <session-id>
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sessions` | List sessions (filter: `workflow_id`, `status`, paginated) |
| `GET` | `/sessions/{id}` | Full session detail with operations |

### Session Response Shape

```json
{
  "id": "sess-abc123",
  "workflow_id": "wf-xyz",
  "execution_id": "exec-456",
  "phase_id": "analyze",
  "status": "completed",
  "agent_provider": "claude",
  "agent_model": "sonnet",
  "total_tokens": 2300,
  "input_tokens": 1500,
  "output_tokens": 800,
  "total_cost_usd": "0.039",
  "started_at": "2026-03-18T10:00:00Z",
  "completed_at": "2026-03-18T10:00:45Z",
  "duration_seconds": 45.2,
  "operations": [
    {
      "operation_id": "op-1",
      "operation_type": "MESSAGE_REQUEST",
      "timestamp": "2026-03-18T10:00:01Z",
      "message_role": "user",
      "message_content": "Analyze the bug..."
    },
    {
      "operation_id": "op-2",
      "operation_type": "TOOL_EXECUTION_STARTED",
      "timestamp": "2026-03-18T10:00:05Z",
      "tool_name": "Read",
      "tool_use_id": "tu-1"
    },
    {
      "operation_id": "op-3",
      "operation_type": "TOOL_EXECUTION_COMPLETED",
      "timestamp": "2026-03-18T10:00:06Z",
      "tool_name": "Read",
      "tool_use_id": "tu-1",
      "duration_seconds": 1.2,
      "success": true
    }
  ]
}
```

### Operation Types

| Type | Description |
|------|-------------|
| `MESSAGE_REQUEST` | Prompt sent to the agent |
| `MESSAGE_RESPONSE` | Agent response |
| `TOOL_EXECUTION_STARTED` | Agent invoked a tool |
| `TOOL_EXECUTION_COMPLETED` | Tool finished |
| `TOOL_BLOCKED` | Tool was safety-blocked |
| `THINKING` | Agent thinking/reasoning step |
| `ERROR` | Error occurred |
| `VALIDATION` | Input/output validation |

## Tool Timeline

Detailed tool execution traces — when each tool was called, how long it took, whether it succeeded.

```bash
# View tool timeline for a session
uv run --package syn-cli syn observe tools <session-id>

# Via API
curl -s "http://localhost:8137/observability/sessions/<session-id>/tools?limit=100" | python -m json.tool
```

Response shape:
```json
{
  "session_id": "sess-abc123",
  "total_executions": 15,
  "executions": [
    {
      "tool_name": "Read",
      "tool_use_id": "tu-1",
      "status": "completed",
      "started_at": "2026-03-18T10:00:05Z",
      "completed_at": "2026-03-18T10:00:06Z",
      "duration_ms": 1200,
      "success": true,
      "tool_input": {"file_path": "/src/auth/middleware.py"},
      "tool_output": "..."
    }
  ]
}
```

**Correlation**: `tool_use_id` links STARTED and COMPLETED events for the same tool invocation.

## Token Metrics

Per-message token usage with cache statistics.

```bash
# View token metrics for a session
uv run --package syn-cli syn observe tokens <session-id>

# Via API
curl -s "http://localhost:8137/observability/sessions/<session-id>/tokens" | python -m json.tool
```

Response shape:
```json
{
  "session_id": "sess-abc123",
  "total_input_tokens": 1500,
  "total_output_tokens": 800,
  "total_tokens": 2300,
  "total_cost_usd": "0.039",
  "cache_creation_tokens": 500,
  "cache_read_tokens": 200
}
```

**Cache tokens**: When Claude caches context, `cache_creation_tokens` shows the initial cost and `cache_read_tokens` shows savings from cache hits.

## Costs

### Cost Model

Default pricing (configurable):
- Input tokens: $0.01 per 1,000
- Output tokens: $0.03 per 1,000

### Querying Costs

```bash
# Overall cost summary
uv run --package syn-cli syn costs summary

# Cost for a specific session
uv run --package syn-cli syn costs session <session-id>

# Cost for a workflow's executions
uv run --package syn-cli syn costs workflow <workflow-id>
```

### Cost Breakdowns Available

The `SessionCost` projection tracks granular cost breakdowns:

| Breakdown | Description |
|-----------|-------------|
| `cost_by_model` | Cost per model (sonnet, opus, haiku) |
| `cost_by_tool` | Cost attributed to each tool |
| `tokens_by_tool` | Token usage per tool |
| `cost_by_tool_tokens` | Token cost per tool |

### Via API

```bash
# Session cost
curl -s "http://localhost:8137/costs/sessions/<session-id>" | python -m json.tool

# Execution cost (aggregated across all phases)
curl -s "http://localhost:8137/costs/executions/<execution-id>" | python -m json.tool
```

## Metrics

Aggregated metrics across sessions and executions.

```bash
# Overall metrics
uv run --package syn-cli syn metrics show

# Metrics for a specific workflow
uv run --package syn-cli syn metrics show --workflow <workflow-id>
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/metrics` | Aggregated platform metrics |
| `GET` | `/metrics?workflow_id=...` | Workflow-specific metrics |

## Event Pipeline (How Data Flows)

```
Agent (Claude CLI in Docker container)
  ↓ writes JSONL
.agentic/analytics/events.jsonl
  ↓ watched by
HookWatcher (file watcher in collector)
  ↓ batches events
Collector Service (POST /events, port 8080)
  ↓ deduplicates (SHA-256 event_id)
  ↓ writes to
TimescaleDB (observability hypertable)
  ↓ subscription
ProjectionManager
  ↓ dispatches to
Projections:
  ├── SessionListProjection (session_summaries)
  ├── SessionCostProjection (session_cost)
  ├── TokenMetricsProjection (token_metrics)
  └── ToolTimelineProjection (tool_timelines)
  ↓ queryable via
API Routes → CLI / Dashboard
```

### Event Types Captured

| Category | Event Types |
|----------|-------------|
| Session | `SESSION_STARTED`, `SESSION_ENDED`, `AGENT_STOPPED` |
| Subagent | `SUBAGENT_STARTED`, `SUBAGENT_STOPPED` |
| Tools | `TOOL_EXECUTION_STARTED`, `TOOL_EXECUTION_COMPLETED`, `TOOL_BLOCKED` |
| Tokens | `TOKEN_USAGE` |
| User | `USER_PROMPT_SUBMITTED`, `NOTIFICATION_SENT` |
| Context | `PRE_COMPACT` |
| Git | `GIT_COMMIT`, `GIT_PUSH_*`, `GIT_BRANCH_*`, `GIT_MERGE_*` |
| Workspace | `WORKSPACE_CREATING`, `WORKSPACE_CREATED`, `WORKSPACE_DESTROYED`, `WORKSPACE_ERROR` |
| Cost | `COST_RECORDED`, `SESSION_COST_FINALIZED` |

## Interpreting Observability Data

### "Why was this session expensive?"

1. Check token metrics — high `output_tokens` usually means verbose responses
2. Check tool timeline — many tool calls accumulate tokens (each call includes context)
3. Check `cost_by_model` — opus is ~10x more expensive than haiku
4. Check `cache_read_tokens` — low cache hits mean repeated context loading

### "Why did this session fail?"

1. Check `sessions show` — look at `error_message` and last operations
2. Check tool timeline — look for `TOOL_BLOCKED` events or failed tools
3. Check the session's execution — was the workspace healthy?

### "What tools did the agent use most?"

1. Check tool timeline — count by `tool_name`
2. Check `tokens_by_tool` in cost breakdown — shows which tools consume most tokens
3. Common pattern: `Read` is used most, `Bash` is most expensive (long outputs)

## Dashboard

The Syn-Dashboard-UI at `http://localhost:5173` (dev) shows:
- Real-time event feed
- Session cost cards with model/tool breakdowns
- Execution cost summaries
- Tool cost breakdowns
- Contribution heatmaps
