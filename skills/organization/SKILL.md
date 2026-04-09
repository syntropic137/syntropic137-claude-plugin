---
name: organization
description: Manage the Syntropic137 Organization→System→Repo hierarchy for cost rollup, health monitoring, and contribution tracking
---

# Organization Management — Syntropic137

When you need to understand where your AI engineering spend is going, or which systems are healthy vs degraded, the organization hierarchy is the structure that makes that possible. Without it, costs and health metrics are a flat list with no grouping.

**NEVER assign a repo to a system without first checking if it's already assigned.** A repo can only belong to one system — assigning without unassigning first will fail silently in some CLI versions.

## When to Use This Skill

Use this when you are: setting up the org/system/repo structure for the first time, tracking costs across a group of related repos, checking system health, or reorganizing repos between systems.

Not needed for listing registered repos quickly — use `/syn-repo` for that. Not needed for GitHub App installation — use the github-automation skill.

## The Hierarchy and Why It Exists

```
Organization  (e.g., "Syntropic137")
  └── System  (e.g., "Backend", "Frontend", "Infrastructure")
       └── Repo  (registered GitHub repository)
```

This structure exists for three reasons:
1. **Cost rollup** — see total AI spend per system, not just per session
2. **Health monitoring** — system-level health aggregates across all its repos (healthy / degraded / failing)
3. **Contribution heatmaps** — team activity patterns across repos, grouped by system

If you're a solo developer on one project, you may only need one org + one system + one repo. The structure scales to large engineering orgs with dozens of repos.

## Setting Up the Hierarchy — 3 Steps

**Step 1: Create an organization.**
```bash
syn organization create --name "MyOrg" --slug "myorg"
```
The slug is used in API paths and must be unique. Most teams only need one organization.

**Step 2: Create systems** to group related repos:
```bash
syn system create --organization <org-id> --name "Backend" --description "API and domain services"
syn system create --organization <org-id> --name "Frontend" --description "React apps"
```

**Step 3: Assign repos to systems.** Repos are auto-registered when the GitHub App fires — you just assign them:
```bash
syn repo assign <repo-id> --system <system-id>
```

List registered repos to find their IDs: `syn github repos` or `curl http://localhost:8137/api/v1/repos`.

## Checking Health and Costs

System health (healthy / degraded / failing across all member repos):
```bash
syn system status <system-id>
```

System cost breakdown:
```bash
syn system cost <system-id>
```

Cross-org overview (all systems, all costs, all health):
```bash
syn insights overview
```

## Read Models Available

| Read Model | Query | Use For |
|-----------|-------|---------|
| `GlobalOverview` | `syn insights overview` | Cross-org health + cost summary |
| `SystemStatus` | `syn system status <id>` | Per-system health (healthy/degraded/failing) |
| `SystemPatterns` | `GET /systems/{id}/patterns` | Execution trends per system |
| `SystemCost` | `syn system cost <id>` | System-level cost aggregation |
| `ContributionHeatmap` | `syn insights heatmap` | Team activity across repos |

## Repo Management

Repos are registered automatically when the GitHub App is installed. Manual registration is only needed for repos where you want tracking but don't have the App installed:

```bash
syn repo assign <repo-id> --system <system-id>
syn repo unassign <repo-id>              # must unassign before reassigning
syn repo health <repo-id>
syn repo cost <repo-id>
syn repo failures <repo-id>
```

## When NOT to Use This Skill

Don't create systems just to satisfy the hierarchy. If you're not actively using cost rollup or health monitoring, the flat default (one org, no systems) is fine. Add structure when the need is real, not in anticipation of future use.

## Escalation Point

If a repo isn't showing up in `syn repo list` after GitHub App installation, check trigger history and App installation status before manually registering. The App fires a `RepoRegisteredEvent` on first webhook — if no events have come in, the App may not be installed on that repo yet.

## Integration

Set up organization hierarchy before configuring trigger rules in github-automation — the system/repo structure is needed for cost attribution in trigger-fired executions. Query costs and health via `/syn-repo` from Claude Code.

## CLI Quick Reference

```bash
syn org list
syn system list
syn system status <system-id>
syn system cost <system-id>
syn github repos
syn repo list
syn insights overview
```
