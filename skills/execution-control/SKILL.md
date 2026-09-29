---
name: execution-control
description: Run workflows, monitor execution progress, use the control plane (cancel/inject), resume failed executions, and troubleshoot failed Syntropic137 executions
---

# Execution Control: Syntropic137

When a workflow execution does something unexpected (runs too long, fails a phase, produces wrong output), you need to understand the execution model before taking action. **NEVER re-run a failed execution without first checking which phase failed and why.** Re-running blindly burns budget and obscures the actual problem.

## When to Use This Skill

Use this when you are: starting a workflow execution, monitoring progress across phases, intervening in a running execution (inject context, cancel), resuming a failed one, or diagnosing a failure. 

Not needed for designing the workflow template itself; use workflow-management for that. Not needed for deep cost or token analysis; use the observability skill.

## The Execution State Machine

Every execution moves through states. Understanding the state tells you what action is available:

```
NOT_STARTED → RUNNING → COMPLETED
                      ↘ FAILED       ─┐
                      ↘ CANCELLED    ─┤ resume → a NEW execution that inherits
                      ↘ INTERRUPTED  ─┘ the completed phases (see below)
```

There is no PAUSED state. It existed until v0.32, but nothing ever read the
pause signal - the call returned 200 and the run continued - so the state, the
events and the commands were all deleted rather than left looking real.

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

### Resume

Resume does **not** continue the same run. It creates a NEW execution that
inherits the phases that completed and restarts at the first one that did not,
so a six-phase run that died in phase five costs you five and six, not all six.

```bash
syn execution resume <execution-id>
syn execution resume <id> --acknowledge-external-effects   # phase five had started; re-running may re-push
syn execution resume <id> --override-cancellation          # the parent was CANCELLED
```

Applies to `FAILED` and `INTERRUPTED`, and to `CANCELLED` only with the
override - a cancel was a decision, so resuming past it needs a fresh one. A
`COMPLETED` run has nothing left to resume. One resume per execution; the
original keeps its record and stays exactly as it was.

The call returns once the resume is ADMITTED. The child is created and started
by a background processor, so watch it with `syn execution show <child-id>`.

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
