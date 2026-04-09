---
name: syn-repo
description: Manage Syntropic137 organizations, systems, and registered repositories — the hierarchy for cost rollup, health monitoring, and repo registration
argument-hint: <list|overview|github> [org|system|repo] [args]
model: sonnet
---

# /syn-repo — Organizations, Systems, and Repos

Use this skill when you need to see the org/system/repo hierarchy, check which repos are registered, or view the platform-wide cost and health overview.

## When to Use This

Use `/syn-repo` when you want to: confirm which repos are registered with the platform, see cross-org cost and health summaries, or check which systems exist.

For **creating and managing** the org/system/repo structure, the organization skill has the full model. For **GitHub App installation** and repo access setup, see the github-automation skill.

## The Hierarchy in Brief

```
Organization → System → Repo
```

This grouping exists so you can roll up costs and health by team or product area. A repo not assigned to a system still works — it just won't appear in system-level cost rollups.

Repos are **auto-registered** when the GitHub App fires its first webhook on that repo. You don't need to manually register them.

## Core Commands

```bash
# Repos
syn github repos                      # all repos accessible to the GitHub App
syn github repos --installation <id>  # scoped to a specific GitHub App installation
curl http://localhost:8137/api/v1/repos  # API fallback

# Organizations
curl http://localhost:8137/api/v1/organizations

# Systems
curl http://localhost:8137/api/v1/systems

# Overview (cross-org health + cost summary)
curl http://localhost:8137/api/v1/organizations/overview
syn insights overview
```

API URL resolves from `SYN_API_URL` → `SYN_PUBLIC_HOSTNAME` in `~/.syntropic137/.env` → `http://localhost:8137`.

## Common Scenarios

**"I installed the GitHub App on a repo but it's not showing up."**
1. `syn github repos` — confirms what the App can see
2. If the repo appears here but not in `curl /api/v1/repos`, trigger a webhook event (push a commit) — registration fires on the first event
3. If the repo doesn't appear in `syn github repos`, the App may not be installed: `npx @syntropic137/setup github-app`

**"I want a cross-org cost and health summary."**
`syn insights overview` or `curl http://localhost:8137/api/v1/organizations/overview` — shows all systems, their health status, and total cost.

**"I want to check costs for one system."**
This is in the organization skill: `syn system cost <system-id>` and `syn system status <system-id>`.

## Errors

On API errors, run `/syn-health`. For the full organization management model (creating orgs, systems, assigning repos), see the organization skill.
