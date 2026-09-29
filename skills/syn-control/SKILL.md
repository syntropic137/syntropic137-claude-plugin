---
name: syn-control
description: Control running Syntropic137 executions; list, cancel, inject context, resume a failed execution, and check status
argument-hint: <list|status|cancel|inject|resume> [execution-id] [args]
model: sonnet
---

# /syn-control: Execution Control

Use this skill when you need to monitor or intervene in a running workflow execution. **Check the execution status before taking any control action**: the state tells you exactly what actions are available.

## When to Use This

Use `/syn-control` when you want to: see what executions are running, inject corrective context into one, cancel an execution that's going wrong, or resume a failed execution so it restarts at the first phase that did not finish.

For **diagnosing a failed execution** in depth, the execution-control skill has the full troubleshooting workflow. For **understanding costs from a session**, use `/syn-insights`.

## The Execution State Machine

Every execution is in one of these states. Actions are only valid in the matching state:

```
RUNNING     → cancel → CANCELLED
RUNNING     → inject → RUNNING (context added, run continues)

FAILED      → resume → a NEW execution, starting at the first unfinished phase
INTERRUPTED → resume → a NEW execution, starting at the first unfinished phase
CANCELLED   → resume --override-cancellation → a NEW execution
```

`NOT_STARTED` and `COMPLETED` accept nothing: one has not begun, the other has
nothing left to run.

**There is no pause.** It existed as a command until v0.32 but nothing ever
acted on the signal - the call returned 200 and the execution ran to
completion - so it was deleted rather than left looking real. To stop a run,
cancel it. To change its direction without stopping it, inject context.

**`resume` does not un-pause.** It creates a NEW execution that inherits the
completed phases and restarts at the first phase that did not finish. The
original stays failed and keeps its record.

## Commands

```bash
syn control list                             # all executions
syn control list --status running            # filter: running, failed, completed
syn control status <execution-id>            # detailed phase breakdown
syn control cancel <execution-id> --reason "wrong workflow"
syn control inject <execution-id> -m "Focus only on the auth module"

syn execution resume <execution-id>          # restart a FAILED run at its first unfinished phase
syn execution resume <id> --acknowledge-external-effects   # the restarted phase may re-push
syn execution resume <id> --override-cancellation          # the run was CANCELLED
```

API fallback (if `syn` CLI not available):
```bash
curl http://localhost:8137/api/v1/executions
curl http://localhost:8137/api/v1/executions?status=running
```

## Common Scenarios

**"I want to check what's running right now."**
`syn control list --status running` shows execution IDs, workflow names, and start times.

**"A workflow is analyzing the wrong area and I want to redirect it without restarting."**
Inject corrective context while it runs - there is nothing to pause first:
`syn control inject <id> -m "Focus only on the auth module"`

**"A six-phase run died in phase five. I do not want to pay for one to four again."**
`syn execution resume <id>` creates a new execution that inherits phases one to
four and restarts at five. Add `--acknowledge-external-effects` if phase five
had already started, since re-running it may repeat a push.

**"An execution has been running for 2 hours and looks stuck."**
1. `syn control status <id>` to identify which phase is stuck
2. Check the phase's session: the session_id is in the status output
3. `/syn-insights tools <session-id>` to check if a tool is hanging
4. If confirmed stuck: `syn control cancel <id> --reason "timeout investigation"`

## Finding Execution IDs

If you don't have the ID:
- `syn control list` for recent executions with IDs
- `/syn-insights sessions` (sessions map 1:1 to execution phases)

## Errors

On API errors, run `/syn-health`. If `syn` CLI is not found: `npx @syntropic137/setup cli`. For deep troubleshooting of failed executions, see the execution-control skill.
