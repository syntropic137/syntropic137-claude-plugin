---
name: troubleshooting-workflow-failures
description: Systematically investigate failed Syntropic137 workflow executions; find the root cause before retrying, diagnose phase failures, blocked tools, budget exhaustion, and workspace errors
---

# Troubleshooting Workflow Failures: Syntropic137

When a workflow execution fails, the instinct is to re-run it and hope it works. **That instinct is wrong.**

**NEVER re-run a failed execution without first identifying which phase failed and why.** Re-running without diagnosis wastes budget, masks the real problem, and produces the same failure, possibly 3 more times before you hit the `max_attempts` limit.

Three re-runs with the same failure = a configuration problem, not bad luck.

## When to Use This Skill

Use this when a workflow execution has `status: failed` or `status: interrupted` and you need to understand why before deciding what to do next.

Not needed for executions that are `RUNNING` but seem slow; use the execution-control skill's monitoring section for that. Not needed for choosing a fix; this skill diagnoses, and the workflow-management skill redesigns.

## The Four Investigation Phases

### Phase 1: Get the Execution Detail

```bash
syn control status <execution-id>
```

Or via API: `curl -sf http://localhost:8137/api/v1/executions/<id> | python3 -m json.tool`

Look at:
- **Which phase has `status: failed`?** That's where the failure happened.
- **What is `error_message`?** This is often the complete answer.
- **What is that phase's `session_id`?** You'll need it in Phase 2.

If `error_message` is clear (e.g., "budget exceeded", "workspace provision failed"), skip to the fix table below. If it's vague or empty, continue to Phase 2.

### Phase 2: Inspect the Session Operations Log

```bash
syn sessions show <session-id>
```

The operations log shows every message and tool call in sequence. Read the last 10-20 operations; the failure signature is almost always visible here. Look for:
- The last tool call before the session ended
- An `ERROR` operation with a message
- An abrupt end with no `SESSION_COMPLETED` event (workspace crash or timeout)

### Phase 3: Trace the Tool Timeline

```bash
syn observe tools <session-id>
```

This gives you precise timing and success/failure for every tool call. Look for:

- **`TOOL_BLOCKED`** entries: the agent tried to use a tool not in the phase's `allowed_tools`. This is the most common cause of "failed immediately" phases.
- **Long `duration_ms`** on a `Bash` tool: a hanging command that eventually caused a timeout.
- **Failed `Read` or `Write` calls**: permission issues or paths that don't exist in the workspace.
- **Repeated calls to the same file**: the agent is looping, usually because a previous step produced unexpected output.

### Phase 4: Check Token and Budget Metrics

```bash
syn observe tokens <session-id>
```

If the session ended abruptly without a clear tool error, budget or context exhaustion is likely:
- High `total_input_tokens` (>100K) with the session cutting off: context window limit hit
- Compare `total_cost_usd` to the phase's `budget_per_trigger_usd` or execution's `max_budget_usd`; if equal, budget was the kill switch

## Failure Patterns and Fixes

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Phase fails immediately | `TOOL_BLOCKED`: tool not in `allowed_tools` | Add the tool to the phase config in the workflow template |
| Phase fails on `Bash` | Command hangs or returns error | Check the bash command in the prompt; add `timeout` or restrict the command |
| Phase times out | `timeout_seconds` too low for the task | Increase `timeout_seconds` in the phase definition |
| Budget exhausted | Cost hit `max_budget_usd` | Increase budget or reduce phase scope; use haiku for cheaper phases |
| Workspace provision fails | Docker image missing or corrupt | `just workspace-build` to rebuild; check Docker disk space |
| Agent loops on same calls | Previous phase output was unexpected format | Inspect the artifact from the previous phase; revise its prompt to produce cleaner output |
| Context window hit | Too much input in a single turn | Restructure prompts to load targeted files rather than scanning broadly |

## Red Flags: Stop and Reassess

If you see any of these, don't keep iterating on the same execution:

- **Three runs, same phase failing with the same error**: the workflow design is wrong, not the execution
- **TOOL_BLOCKED on a tool that's obviously needed**: the `allowed_tools` list in the phase config needs to be reviewed; running again won't fix it
- **Workspace provision failing repeatedly**: infrastructure problem; run `just health-check` and `just workspace-build` before any more executions

## After Diagnosing

Once you've identified the root cause:
- **Tool blocked / wrong tools**: edit the workflow template's phase `allowed_tools` (workflow-management skill)
- **Budget too low**: re-run with `--max-budget-usd <higher>` or edit the phase config
- **Workspace issue**: fix infrastructure first (platform-ops skill), then re-run
- **Prompt producing bad output**: revise the phase `prompt_template` and validate the YAML before re-registering

## Integration

This skill follows execution-control (which runs and monitors executions) and feeds back into workflow-management (which redesigns templates). Use `/syn-insights` for quick session and cost queries during investigation.
