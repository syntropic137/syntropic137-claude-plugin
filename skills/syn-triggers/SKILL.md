---
name: syn-triggers
description: Manage Syntropic137 GitHub webhook trigger rules — list, register, enable, pause, and delete triggers that fire workflows on GitHub events
argument-hint: <list|register|enable|pause|delete> [args]
model: sonnet
---

# /syn-triggers — Webhook Trigger Management

Use this skill when you need to create, view, or manage the trigger rules that automatically fire Syntropic137 workflows on GitHub events.

## When to Use This

Use `/syn-triggers` when you want to: see what triggers are active on a repo, register a new trigger, pause a noisy trigger, check why a trigger didn't fire, or delete a rule you no longer need.

For the **full setup story** — GitHub App installation, webhook delivery via Cloudflare, input mapping from payload fields, and safety limit design — the github-automation skill has the complete picture.

## The Trigger Rule Pattern

A trigger rule is: *event + conditions + safety limits + input mapping → workflow execution*.

When GitHub sends a webhook event, the platform checks:
1. Does the event type match?
2. Do all conditions match the payload?
3. Do safety guards pass? (concurrency, max_attempts, cooldown, daily_limit)

If all pass, the workflow fires with inputs mapped from the webhook payload.

**Always set safety limits when registering.** Without them, a busy PR bot or CI loop can fire your trigger hundreds of times a day.

## Core Commands

```bash
syn triggers list
syn triggers list --repository owner/repo
syn triggers register \
  --name "pr-review" \
  --event pull_request \
  --repository owner/repo \
  --workflow <workflow-id> \
  --condition action=opened \
  --budget 5.00 \
  --cooldown 300
syn triggers enable <name> --repository owner/repo
syn triggers pause <id> --reason "investigating false positives"
syn triggers resume <id>
syn triggers history <trigger-id>       # fire history with block reasons
syn triggers disable-all                # emergency stop for all triggers
syn triggers delete <id>
```

Supported events: `push`, `pull_request`, `issues`, `issue_comment`, `check_run`, `workflow_run`

## Common Scenarios

**"I want to auto-review PRs on my repo."**
1. Find the review workflow ID: `syn workflow list`
2. Register: `syn triggers register --name "pr-review" --event pull_request --repository owner/repo --workflow <id> --condition action=opened --budget 2.00 --cooldown 300`
3. Verify: `syn triggers list --repository owner/repo`

**"My trigger didn't fire — what happened?"**
`syn triggers history <trigger-id>` — blocked entries show the exact guard and reason:
- `concurrency` — execution already running for same trigger + PR
- `max_attempts` — that PR already hit the fire limit
- `cooldown` — fired too recently
- `daily_limit` — daily cap reached
- `conditions_not_met` — payload didn't match conditions

**"A trigger is firing too often and I need to stop it temporarily."**
`syn triggers pause <id> --reason "too noisy"` — stops firing without deleting the rule. Resume later with `syn triggers resume <id>`.

## Delete a Trigger

```bash
syn triggers delete <id>
```

If the `syn` CLI doesn't support delete yet: `curl -X DELETE http://localhost:8137/api/v1/triggers/<id>`

## Errors

On API errors, run `/syn-health`. If GitHub events aren't reaching the platform, verify the GitHub App webhook delivery: `npx @syntropic137/setup github-app`. For the full trigger design guide, see the github-automation skill.
