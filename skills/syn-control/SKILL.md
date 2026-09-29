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

Every `resume` arrow CREATES a separate execution; none of them moves the
original, which keeps its terminal status and its record. `--override-cancellation`
is required on the third, and `--acknowledge-external-effects` on any of them
whose restarted phase had already begun.

```
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

**Listing and inspecting live on `syn execution`, not `syn control`.** The
control group has exactly four commands: `cancel`, `status`, `inject`, `stop`.

```bash
syn execution list                           # all executions
syn execution list --status running          # filter: running, failed, completed
syn execution show <execution-id>            # phase-by-phase breakdown

syn control status <execution-id>            # control state ONLY - two lines, no phases
syn control cancel <execution-id> --reason "wrong workflow" --force
syn control inject <execution-id> -m "Focus only on the auth module"

syn execution resume <execution-id>          # restart a FAILED run at its first unfinished phase
syn execution resume <id> --acknowledge-external-effects   # the restarted phase may re-push
syn execution resume <id> --override-cancellation          # the run was CANCELLED
```

`cancel` and `stop` REFUSE without `--force`: they print
`Use --force to confirm ...` and change nothing. A scripted cancel that omits
it records a cancel that never happened.

API fallback (if `syn` CLI not available):
```bash
curl http://localhost:8137/api/v1/executions
curl http://localhost:8137/api/v1/executions?status=running
```

## Common Scenarios

**"I want to check what's running right now."**
`syn execution list --status running` shows execution IDs, workflow names, and start times.

**"A workflow is analyzing the wrong area and I want to redirect it without restarting."**
Inject corrective context while it runs - there is nothing to pause first:
`syn control inject <id> -m "Focus only on the auth module"`

**"A six-phase run died in phase five. I do not want to pay for one to four again."**
1. `syn execution show <id>` first, and look at the phase the resume will
   restart at - the first one that did not complete.
2. If that phase EVER started, including on an earlier retry, the resume is
   refused without `--acknowledge-external-effects`. "Started" is the test,
   not "was the phase the failure named".
3. If the parent is CANCELLED, add `--override-cancellation` as well. The two
   flags are independent; needing one does not imply the other.

```bash
syn execution resume <id> --acknowledge-external-effects
```

The new execution inherits phases one to four and restarts at five. Do not
lead with the bare form and retry on refusal: the refusal text is the only
place the reason appears, and an agent that retries blindly will add flags it
has not reasoned about.

**"An execution has been running for 2 hours and looks stuck."**
1. `syn execution show <id>` to identify which phase is stuck. `syn control
   status` will NOT tell you - it prints the execution id and its state, and
   nothing about phases.
2. Check that phase's session: the session_id is in the `show` output
3. `/syn-insights tools <session-id>` to check if a tool is hanging
4. If confirmed stuck: `syn control cancel <id> --reason "timeout investigation" --force`

## Finding Execution IDs

If you don't have the ID:
- `syn execution list` for recent executions with IDs
- `/syn-insights sessions` (sessions map 1:1 to execution phases)

## Errors

On API errors, run `/syn-health`. If `syn` CLI is not found: `npx @syntropic137/setup cli`. For deep troubleshooting of failed executions, see the execution-control skill.
