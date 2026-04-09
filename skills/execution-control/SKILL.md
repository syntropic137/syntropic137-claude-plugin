---
name: execution-control
description: Run workflows, monitor execution progress, use the control plane (pause/resume/cancel/inject), and troubleshoot failed Syntropic137 executions
---

# Execution Control: Syntropic137

When a workflow execution does something unexpected (runs too long, fails a phase, produces wrong output), you need to understand the execution model before taking action. **NEVER re-run a failed execution without first checking which phase failed and why.** Re-running blindly burns budget and obscures the actual problem.

## When to Use This Skill

Use this when you are: starting a workflow execution, monitoring progress across phases, intervening in a running execution (pause, inject context, cancel), or diagnosing a failure. 

Not needed for designing the workflow template itself; use workflow-management for that. Not needed for deep cost or token analysis; use the observability skill.

## The Execution State Machine

Every execution moves through states. Understanding the state tells you what action is available:

```
NOT_STARTED → RUNNING → COMPLETED
                      ↘ FAILED
                      ↘ PAUSED → RUNNING (on resume)
                      ↘ CANCELLED
                      ↘ INTERRUPTED (partial state preserved)
```

Each **phase** within an execution has its own state: `PENDING → RUNNING → COMPLETED | FAILED | SKIPPED`.

The system uses the **Processor To-Do List** pattern: crash-resilient execution where the aggregate is the sole decision-maker. If the platform restarts mid-execution, it picks up from the last completed step automatically. Handlers are idempotent.

## Running a Workflow

```bash
syn workflow run <workflow-id> --task "Fix the auth timeout bug"
syn workflow run <workflow-id> --task "Review PR #42" --input repository=owner/repo
syn run <workflow-id> -t "Implement retry logic"   # short alias
```

With budget control: add `--max-budget-usd 5.00` to cap spend per execution.

Via API: `POST /api/v1/workflows/<id>/execute` with `{"task": "...", "inputs": {...}, "max_budget_usd": 5.00}`.

## Monitoring Progress

Check a specific execution: `syn control status <execution-id>`

List all active executions: `curl -sf http://localhost:8137/api/v1/executions | python3 -m json.tool`

Filter by status: `curl -sf "http://localhost:8137/api/v1/executions?status=running"`

The execution detail shows each phase's status, session ID, cost, and duration; this is your first stop when something looks wrong.

## Control Plane: Intervening in a Running Execution

### Pause and Resume

Pause is **graceful**: the agent finishes its current tool call before halting:

```bash
syn control pause <execution-id> --reason "reviewing intermediate results"
syn control resume <execution-id>
```

Use pause when you want to inspect artifacts from completed phases before proceeding. The execution stays alive; all state is preserved.

### Inject Context

Send additional instructions to the running agent without stopping it:

```bash
curl -X POST http://localhost:8137/api/v1/executions/<id>/inject \
  -d '{"message": "Focus only on the auth module, skip database changes", "role": "user"}'
```

Inject when the agent is heading in the wrong direction and you want to steer it without restarting. Use `"role": "system"` for budget or constraint warnings.

### Cancel

Cancel is permanent; it stops the execution and marks phases as SKIPPED:

```bash
syn control cancel <execution-id> --reason "wrong workflow template used"
```

## Troubleshooting a Failed Execution: 4 Steps

**Step 1: Get the execution detail.** Run `syn control status <execution-id>` or `curl -sf http://localhost:8137/api/v1/executions/<id>`. Find which phase has `status: failed` and read its `error_message`.

**Step 2: Check the failing phase's session.** Each phase has a `session_id`. Run `syn sessions show <session-id>` to see the operations timeline: what the agent was doing when it failed.

**Step 3: Check the tool timeline.** Run `syn observe tools <session-id>` (or `/syn-insights tools <session-id>`). Look for `TOOL_BLOCKED` events or tools that returned errors. This tells you *what* the agent was trying to do.

**Step 4: Check token metrics.** Run `syn observe tokens <session-id>`. If input tokens spiked, the context window may have been overwhelmed. If the session ended abruptly, it may have hit the phase `timeout_seconds`.

### Common Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Phase stuck RUNNING | Timeout exceeded | Increase `timeout_seconds` in phase config |
| FAILED with budget error | `max_budget_usd` hit | Increase budget or reduce scope |
| FAILED immediately | Workspace provision failed | `just workspace-build` to rebuild image |
| TOOL_BLOCKED in tool timeline | Tool not in `allowed_tools` | Add tool to phase config |

## Escalation Point

If an execution fails 3 times with the same error pattern, **stop re-running and reassess the workflow design.** A repeated failure is a signal that the phase config is wrong (wrong model, insufficient budget, blocked tools), not that the agent needs another chance.

## Integration

Design the template with workflow-management, run and control here, then analyze costs and patterns with the observability skill. Use `/syn-control` for interactive control from Claude Code.
