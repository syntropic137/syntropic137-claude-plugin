---
name: syn-triggers
description: Manage Syntropic137 GitHub webhook trigger rules — list, register, enable, pause, and delete triggers that fire workflows on GitHub events
argument-hint: <list|register|enable|pause|delete> [args]
model: sonnet
---

# /syn-triggers — Webhook Trigger Rules

Use this skill to set up and manage trigger rules that automatically fire Syntropic137 workflows when GitHub events occur (e.g., a PR opened, a commit pushed). All operations go through the `syn` CLI. If `syn` is not installed, run `npx @syntropic137/setup cli` first.

## List Triggers

See all registered trigger rules, optionally scoped to a repository:

```bash
syn triggers list
syn triggers list --repository owner/repo
```

## Register a New Trigger

Wire a GitHub event to a workflow. The `--event` field is the GitHub webhook event type:

```bash
syn triggers register \
  --name "pr-review" \
  --event pull_request \
  --repository owner/repo \
  --workflow <workflow-id>
```

Supported events: `push`, `pull_request`, `issues`, `issue_comment`, `check_run`, `workflow_run`

Get the workflow ID from `syn workflow list` or `/syn-workflow list`.

## Enable a Paused Trigger

```bash
syn triggers enable <name> --repository owner/repo
```

## Pause a Trigger

Pausing suspends the trigger without deleting it — useful when investigating issues:

```bash
syn triggers pause <id>
syn triggers pause <id> --reason "investigating false positives"
```

## Delete a Trigger

Deletion is permanent. If `syn` doesn't support delete yet, call the API directly:

```bash
curl -X DELETE http://localhost:8137/api/v1/triggers/<trigger-id>
```

Resolve the API URL from `SYN_API_URL` env var, or `SYN_PUBLIC_HOSTNAME` in `~/.syntropic137/.env`, falling back to `http://localhost:8137`.

## Typical Workflow

1. Find the workflow ID you want to fire: `syn workflow list`
2. Register the trigger against the target repo and event
3. Verify it appears: `syn triggers list --repository owner/repo`
4. Test by triggering the GitHub event (e.g., open a PR)
5. Watch the execution: `syn control list --status running`

## Errors

On API errors, run `/syn-health` to check platform status. If GitHub events aren't firing, verify the GitHub App webhook is configured: `npx @syntropic137/setup github-app`
