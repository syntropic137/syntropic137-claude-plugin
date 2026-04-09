---
name: syn-repo
description: Manage Syntropic137 organizations, systems, and registered repositories — the hierarchy for cost rollup, health monitoring, and repo registration
argument-hint: <list|overview|github> [org|system|repo] [args]
model: sonnet
---

# /syn-repo — Organizations, Systems, and Repos

Syntropic137 organizes cost rollup and health monitoring in a three-level hierarchy: **organizations → systems → repositories**. Repos are auto-registered when the GitHub App is installed on them.

The API URL defaults to `http://localhost:8137`. Read `SYN_PUBLIC_HOSTNAME` from `~/.syntropic137/.env` if a custom hostname is configured, or use the `SYN_API_URL` environment variable.

## List Repositories

If `syn` CLI is available:

```bash
syn github repos
```

Fallback via API:

```bash
curl http://localhost:8137/api/v1/repos
```

## List Organizations

```bash
curl http://localhost:8137/api/v1/organizations
```

## List Systems

```bash
curl http://localhost:8137/api/v1/systems
```

## Platform Overview

Cross-org health summary with cost rollup:

```bash
curl http://localhost:8137/api/v1/organizations/overview
```

## GitHub App Repos

List all repos accessible to the installed GitHub App (useful to verify which repos are connected):

```bash
syn github repos
syn github repos --installation <installation-id>   # for a specific GitHub App installation
```

## Repos Not Showing Up?

Repos are auto-registered when the GitHub App webhook fires. If a repo is missing:

1. Verify the GitHub App is installed on the repo: check `github.com/apps/<your-app>/installations`
2. Re-run setup if needed: `npx @syntropic137/setup github-app`
3. Check `syn github repos` to confirm the App can see the repo
4. Trigger a webhook event (push a commit) to force registration

## Errors

On API errors, run `/syn-health` to diagnose platform status.
