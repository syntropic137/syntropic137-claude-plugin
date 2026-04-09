---
name: execution-control
description: Run workflows, monitor execution progress, use the control plane (pause/resume/cancel/inject), and troubleshoot failed Syntropic137 executions
user-invocable: false
---

# Execution Control — Syntropic137

Use this knowledge when the user wants to run workflows, monitor execution progress, pause/resume/cancel executions, or understand why an execution failed.

## Running a Workflow

### Via CLI

```bash
# Run a workflow with inputs
syn workflow run <workflow-id> \
  --input issue_url=https://github.com/org/repo/issues/42 \
  --input priority=high

# Short alias
syn run <workflow-id> --input issue_url=...

# With provider override
syn workflow run <workflow-id> --provider claude

# Check execution status
syn workflow status <execution-id>
```

### Via API

```bash
# Start execution
curl -X POST http://localhost:8137/workflows/<workflow-id>/execute \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"issue_url": "https://github.com/org/repo/issues/42"},
    "provider": "claude",
    "max_budget_usd": 5.00
  }'

# Response
{
  "execution_id": "exec-abc123",
  "workflow_id": "wf-xyz",
  "status": "running",
  "started_at": "2026-03-18T10:00:00Z"
}
```

## Monitoring Executions

### List Executions

```bash
# All executions
syn sessions list

# Filter by status
curl -s "http://localhost:8137/executions?status=running" | python -m json.tool
curl -s "http://localhost:8137/executions?status=failed" | python -m json.tool
```

### Execution Detail

```bash
# Full detail with phase breakdown
curl -s http://localhost:8137/executions/<execution-id> | python -m json.tool
```

Response shape:
```json
{
  "workflow_execution_id": "exec-abc123",
  "workflow_id": "wf-xyz",
  "workflow_name": "Fix Bug in Auth Service",
  "status": "running",
  "started_at": "2026-03-18T10:00:00Z",
  "completed_at": null,
  "phases": [
    {
      "phase_id": "analyze",
      "name": "Bug Analysis",
      "status": "completed",
      "session_id": "sess-111",
      "artifact_id": "art-aaa",
      "input_tokens": 1500,
      "output_tokens": 800,
      "duration_seconds": 45.2,
      "cost_usd": "0.039",
      "started_at": "2026-03-18T10:00:00Z",
      "completed_at": "2026-03-18T10:00:45Z"
    },
    {
      "phase_id": "implement",
      "name": "Implementation",
      "status": "running",
      "session_id": "sess-222",
      "started_at": "2026-03-18T10:00:46Z"
    }
  ],
  "total_input_tokens": 1500,
  "total_output_tokens": 800,
  "total_tokens": 2300,
  "total_cost_usd": "0.039",
  "total_duration_seconds": 45.2,
  "artifact_ids": ["art-aaa"]
}
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/executions` | List all executions (filter: `status`, paginated) |
| `GET` | `/executions/{id}` | Full execution detail with phases |
| `POST` | `/workflows/{id}/execute` | Start new execution |
| `GET` | `/executions/{id}/state` | Current execution state |

## Control Plane

Control a running execution via HTTP or WebSocket.

### Pause / Resume

```bash
# Pause (graceful — waits for current tool to finish)
syn control pause <execution-id> --reason "Reviewing intermediate results"

# Via API
curl -X POST http://localhost:8137/executions/<execution-id>/pause \
  -d '{"reason": "Reviewing intermediate results"}'

# Resume
syn control resume <execution-id>

# Via API
curl -X POST http://localhost:8137/executions/<execution-id>/resume
```

### Cancel

```bash
# Cancel (stops execution, marks as cancelled)
syn control cancel <execution-id> --reason "Wrong workflow template"

# Via API
curl -X POST http://localhost:8137/executions/<execution-id>/cancel \
  -d '{"reason": "Wrong workflow template"}'
```

### Interrupt (SIGINT)

```bash
# Interrupt (preserves partial state, like Ctrl+C)
syn control interrupt <execution-id>
```

### Inject Context

Send additional context or instructions to a running agent:

```bash
# Via API — inject a user message
curl -X POST http://localhost:8137/executions/<execution-id>/inject \
  -d '{"message": "Focus on the auth middleware, not the database layer", "role": "user"}'

# System-level injection
curl -X POST http://localhost:8137/executions/<execution-id>/inject \
  -d '{"message": "Budget limit approaching, wrap up current phase", "role": "system"}'
```

### WebSocket Control

For real-time bidirectional control:

```
ws://localhost:8137/ws/control/<execution-id>
```

## Execution Statuses

| Status | Description |
|--------|-------------|
| `NOT_STARTED` | Created but not yet running |
| `RUNNING` | Actively executing phases |
| `PAUSED` | Temporarily halted (resumable) |
| `COMPLETED` | All phases finished successfully |
| `FAILED` | A phase failed (see `error_message`) |
| `CANCELLED` | Manually cancelled by user |
| `INTERRUPTED` | SIGINT with partial state preserved |

### Phase Statuses

| Status | Description |
|--------|-------------|
| `PENDING` | Not yet started |
| `RUNNING` | Currently executing |
| `COMPLETED` | Finished successfully |
| `FAILED` | Failed (see error) |
| `SKIPPED` | Skipped (e.g., after cancel) |

## How Execution Works Internally

The system uses the **Processor To-Do List** pattern for crash-resilient multi-phase execution:

```
Start Execution
  → WorkflowExecutionAggregate emits WorkflowExecutionStartedEvent
  → ExecutionTodoProjection queues: PROVISION_WORKSPACE for phase 1

Phase Loop:
  1. PROVISION_WORKSPACE
     → WorkspaceProvisionHandler creates Docker container
     → Injects tokens via Envoy sidecar proxy
     → Aggregate emits WorkspaceProvisionedForPhaseEvent
     → Todo: EXECUTE_AGENT

  2. EXECUTE_AGENT
     → AgentExecutionHandler runs Claude CLI in container
     → Captures JSONL output (tokens, tool calls, errors)
     → Aggregate emits AgentExecutionCompletedEvent
     → Todo: COLLECT_ARTIFACTS

  3. COLLECT_ARTIFACTS
     → ArtifactCollectionHandler saves outputs to MinIO
     → Aggregate emits ArtifactsCollectedForPhaseEvent
     → Aggregate checks phase_order_map for next phase
     → If next phase exists: emits NextPhaseReadyEvent → loop back to step 1
     → If no more phases: emits WorkflowCompletedEvent → done
```

**Key properties:**
- **Crash-resilient**: If the processor crashes, the to-do list persists. On restart, it picks up from the last completed step.
- **Aggregate is the decision-maker**: The aggregate decides "what's next" — never the processor.
- **Handlers are idempotent**: Re-running a handler (after crash) is safe.

## Troubleshooting Failed Executions

### 1. Check execution detail

```bash
curl -s http://localhost:8137/executions/<execution-id> | python -m json.tool
```

Look at:
- `status`: Should tell you the overall state
- `phases[].status`: Which phase failed
- `phases[].error_message`: Why it failed
- `phases[].session_id`: Session to investigate

### 2. Check the agent session

```bash
syn sessions show <session-id>
syn observe tools <session-id>
syn observe errors <session-id>
```

### 3. Check workspace logs

If the workspace is still alive:
```bash
docker logs <container-id>
```

### 4. Common failure reasons

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Phase stuck in RUNNING | Agent timed out | Check `timeout_seconds` in phase config |
| FAILED with token error | Budget exceeded | Increase `max_budget_usd` or reduce scope |
| FAILED immediately | Workspace provision failed | Check Docker, rebuild image with `just workspace-build` |
| FAILED with tool error | Blocked tool | Check `allowed_tools` in phase config |

## Execution Metrics

After completion, each execution has aggregated metrics:

```json
{
  "total_phases": 3,
  "completed_phases": 3,
  "total_input_tokens": 15000,
  "total_output_tokens": 8000,
  "total_tokens": 23000,
  "total_cost_usd": "0.39",
  "total_duration_seconds": 180.5,
  "artifact_ids": ["art-1", "art-2", "art-3"]
}
```

Use `/syn-costs` or `/syn-metrics` to view aggregated cost and performance data across executions.

## CLI Quick Reference

```bash
# Control plane
syn control status <execution-id>
syn control pause <execution-id> --reason "investigating"
syn control resume <execution-id>
syn control cancel <execution-id> --reason "wrong workflow"

# List executions (via API)
curl -sf http://localhost:8137/api/v1/executions | python3 -m json.tool
curl -sf "http://localhost:8137/api/v1/executions?status=running" | python3 -m json.tool

# Execution detail
curl -sf http://localhost:8137/api/v1/executions/<execution-id> | python3 -m json.tool
```

Use `/syn-control` to run these commands interactively from Claude Code.
