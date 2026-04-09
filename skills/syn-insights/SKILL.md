---
name: syn-insights
description: Query Syntropic137 observability data — sessions, artifacts, token costs, tool timelines, and system-wide insights
argument-hint: <overview|sessions|artifacts|costs|tools|tokens> [args]
model: sonnet
---

# /syn-insights — Observability

Use this skill to explore what Syntropic137 agents have been doing — sessions, artifacts produced, token costs, and tool call timelines. Data is served from the platform API.

The API URL defaults to `http://localhost:8137`. If a custom hostname is configured, read `SYN_PUBLIC_HOSTNAME` from `~/.syntropic137/.env`, or check the `SYN_API_URL` environment variable.

## Platform Overview

A cross-org health and cost summary:

```bash
curl http://localhost:8137/api/v1/organizations/overview
```

## Sessions

List all sessions:

```bash
curl http://localhost:8137/api/v1/sessions
```

Filter by workflow or status:

```bash
curl "http://localhost:8137/api/v1/sessions?workflow_id=<id>"
curl "http://localhost:8137/api/v1/sessions?status=running"
curl "http://localhost:8137/api/v1/sessions?workflow_id=<id>&status=completed"
```

Show a specific session:

```bash
curl http://localhost:8137/api/v1/sessions/<session-id>
```

Statuses: `running`, `completed`, `failed`, `paused`

## Artifacts

List all artifacts, or filter to a workflow:

```bash
syn artifacts list
syn artifacts list --workflow <workflow-id>
```

Show a specific artifact or its raw content:

```bash
syn artifacts show <artifact-id>
syn artifacts content <artifact-id> --raw
```

## Costs

Overall cost summary:

```bash
curl http://localhost:8137/api/v1/costs/summary
```

Cost breakdown for a specific session or execution:

```bash
curl http://localhost:8137/api/v1/costs/sessions/<session-id>
curl http://localhost:8137/api/v1/costs/executions/<execution-id>
```

## Tool Call Timeline

See every tool call made during a session, in order — useful for debugging agent behavior:

```bash
curl "http://localhost:8137/api/v1/events/sessions/<session-id>/tools?limit=100"
```

Increase `limit` if the session was long (default 100).

## Token Usage

Token metrics for a session (input, output, cache hit/miss breakdown):

```bash
curl http://localhost:8137/api/v1/events/sessions/<session-id>/tokens
```

## Piping JSON output

Pipe any API response through `python3 -m json.tool` for readable formatting:

```bash
curl http://localhost:8137/api/v1/sessions | python3 -m json.tool
```

## Errors

On API errors, run `/syn-health` to diagnose platform status. If `syn` CLI is not found, install with: `npx @syntropic137/setup cli`
