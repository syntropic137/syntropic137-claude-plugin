---
name: syn-control
description: Control running Syntropic137 executions — list, pause, resume, cancel, and check status of workflow executions
argument-hint: <list|status|pause|resume|cancel> [execution-id] [args]
model: sonnet
---

# /syn-control — Execution Control

Use this skill when you need to monitor or intervene in a running workflow execution. **Check the execution status before taking any control action** — the state tells you exactly what actions are available.

## When to Use This

Use `/syn-control` when you want to: see what executions are running, pause an execution to review intermediate results, inject corrective context, resume after review, or cancel an execution that's going wrong.

For **diagnosing a failed execution** in depth, the execution-control skill has the full troubleshooting workflow. For **understanding costs from a session**, use `/syn-insights`.

## The Execution State Machine

Every execution is in one of these states. Actions are only valid in the matching state:

```
RUNNING  → pause → PAUSED → resume → RUNNING
RUNNING  → cancel → CANCELLED
PAUSED   → cancel → CANCELLED
```

`NOT_STARTED`, `COMPLETED`, `FAILED`, `INTERRUPTED` are terminal or pre-start states — no control actions apply.

## Commands

```bash
syn control list                             # all executions
syn control list --status running            # filter: running, paused, failed, completed
syn control status <execution-id>            # detailed phase breakdown
syn control pause <execution-id>
syn control pause <execution-id> --reason "reviewing phase 2 output"
syn control resume <execution-id>
syn control cancel <execution-id> --reason "wrong workflow"
```

API fallback (if `syn` CLI not available):
```bash
curl http://localhost:8137/api/v1/executions
curl http://localhost:8137/api/v1/executions?status=running
```

## Common Scenarios

**"I want to check what's running right now."**
`syn control list --status running` — shows execution IDs, workflow names, start times.

**"A workflow is analyzing the wrong area — I want to redirect it without restarting."**
1. `syn control pause <id>` — waits for the current tool call to finish
2. Inject corrective context: `curl -X POST http://localhost:8137/api/v1/executions/<id>/inject -d '{"message": "Focus only on the auth module", "role": "user"}'`
3. `syn control resume <id>`

**"An execution has been running for 2 hours and looks stuck."**
1. `syn control status <id>` — which phase is stuck?
2. Check the phase's session: the session_id is in the status output
3. `/syn-insights tools <session-id>` — is a tool hanging?
4. If confirmed stuck: `syn control cancel <id> --reason "timeout investigation"`

## Finding Execution IDs

If you don't have the ID:
- `syn control list` — recent executions with IDs
- `/syn-insights sessions` — sessions map 1:1 to execution phases

## Errors

On API errors, run `/syn-health`. If `syn` CLI is not found: `npx @syntropic137/setup cli`. For deep troubleshooting of failed executions, see the execution-control skill.
