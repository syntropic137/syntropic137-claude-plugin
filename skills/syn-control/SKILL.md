---
name: syn-control
description: Control running Syntropic137 executions — list, pause, resume, cancel, and check status of workflow executions
argument-hint: <list|status|pause|resume|cancel> [execution-id] [args]
model: sonnet
---

# /syn-control — Execution Control

Use this skill to monitor and control in-flight Syntropic137 workflow executions. All control operations go through the `syn` CLI. If `syn` is not installed, run `npx @syntropic137/setup cli` first.

## List and Status

To see all active executions:

```bash
syn control list
syn control list --status running     # filter: running, paused, failed, completed
```

To check the status of a specific execution:

```bash
syn control status <execution-id>
```

If the `syn` CLI is not available, fall back to the platform API directly:

```bash
curl http://localhost:8137/api/v1/executions
curl http://localhost:8137/api/v1/executions?status=running
```

The API URL defaults to `http://localhost:8137`. If a custom hostname is configured, read it from `~/.syntropic137/.env` (`SYN_PUBLIC_HOSTNAME`) or check the `SYN_API_URL` environment variable.

## Pause an Execution

Pausing lets you inspect intermediate state, review artifacts, or hold while you adjust something — then resume later:

```bash
syn control pause <execution-id>
syn control pause <execution-id> --reason "reviewing intermediate results"
```

## Resume a Paused Execution

```bash
syn control resume <execution-id>
```

## Cancel an Execution

Cancellation is permanent. Use this when the run is incorrect or no longer needed:

```bash
syn control cancel <execution-id>
syn control cancel <execution-id> --reason "wrong workflow triggered"
```

## Finding Execution IDs

If you don't have the execution ID handy:

1. Run `syn control list` to see recent executions with their IDs
2. Or check `/syn-insights sessions` — sessions map 1:1 to executions
3. Or run `syn workflow status <execution-id>` if you launched via `/syn-workflow run`

## Errors

On API errors, run `/syn-health` to check platform status. If `syn` CLI is not found, install with: `npx @syntropic137/setup cli`
