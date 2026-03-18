# Organization & GitHub Integration — Syntropic137

Use this knowledge when the user wants to manage organizations, systems, repositories, GitHub App integrations, or webhook trigger rules.

## Organization Hierarchy

```
Organization (top-level entity)
  └── System (logical grouping, e.g., "Backend", "Frontend", "Infrastructure")
       └── Repo (registered GitHub repository)
```

### Organizations

```bash
# Via API
curl -s http://localhost:8000/organizations | python -m json.tool
curl -X POST http://localhost:8000/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Syntropic137", "slug": "syn137"}'
```

### Systems

Systems group related repos for health monitoring and cost rollup.

```bash
# List systems in an org
curl -s "http://localhost:8000/systems?organization_id=<org-id>" | python -m json.tool

# Create system
curl -X POST http://localhost:8000/systems \
  -d '{"organization_id": "<org-id>", "name": "Backend Services", "description": "API and domain services"}'
```

### Repositories

Repos are registered from GitHub App installations. They can be assigned to systems.

```bash
# List repos
curl -s "http://localhost:8000/repos?organization_id=<org-id>" | python -m json.tool

# Register repo (usually automatic via GitHub App)
curl -X POST http://localhost:8000/repos \
  -d '{
    "organization_id": "<org-id>",
    "provider": "github",
    "provider_repo_id": "123456",
    "full_name": "syntropic137/syntropic137",
    "owner": "syntropic137",
    "default_branch": "main",
    "installation_id": "<installation-id>"
  }'

# Assign repo to system
curl -X POST http://localhost:8000/repos/<repo-id>/assign \
  -d '{"system_id": "<system-id>"}'

# Unassign from system
curl -X POST http://localhost:8000/repos/<repo-id>/unassign
```

### Read Models

The organization context has rich read models for operational intelligence:

| Read Model | Purpose |
|-----------|---------|
| `GlobalOverview` | Cross-org system and repo overview with cost rollup |
| `SystemStatus` | Per-system health across repos (healthy/degraded/failing) |
| `SystemPatterns` | Execution patterns and trends |
| `SystemCost` | System-level cost aggregation |
| `ContributionHeatmap` | Team contribution patterns |

## GitHub App Integration

### How It Works

Syntropic137 uses a GitHub App for:
1. **Repository access** — Clone repos into isolated workspaces
2. **Webhook triggers** — Automatically start workflows on push, PR, issue events
3. **Status reporting** — Report execution results back to PRs

### Installation Lifecycle

```
GitHub App installed on org/repo
  → AppInstalledEvent (InstallationAggregate)
  → Repos registered automatically
  → Webhooks start flowing

Revoked:
  → InstallationRevokedEvent
  → Triggers paused
```

### Token Refresh

The Installation aggregate tracks token refreshes as telemetry events — these are NOT replayed during state reconstitution (they're purely observational).

### Setup

GitHub App is configured during `just onboard` or manually:
1. Create GitHub App (manifest flow — `just onboard-dev` handles this)
2. Set environment variables: `GITHUB_APP_ID`, `SYN_GITHUB_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`
3. Install on your org/repos via GitHub UI

## Trigger Rules

Trigger rules automate workflow execution based on GitHub webhook events.

### Concept

A trigger rule says: "When event X happens on repo Y (matching conditions Z), start workflow W with inputs mapped from the webhook payload."

### Creating Triggers

```bash
# Via CLI
uv run --package syn-cli syn triggers create "PR Review Bot" \
  --event pull_request \
  --repo syntropic137/syntropic137 \
  --workflow <workflow-id> \
  --condition "action=opened" \
  --condition "base.ref=main"

# Via API
curl -X POST http://localhost:8000/triggers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PR Review Bot",
    "event": "pull_request",
    "repository": "syntropic137/syntropic137",
    "installation_id": "<installation-id>",
    "workflow_id": "<workflow-id>",
    "conditions": [
      {"field": "action", "operator": "equals", "value": "opened"},
      {"field": "base.ref", "operator": "equals", "value": "main"}
    ],
    "input_mapping": {
      "pr_url": "pull_request.html_url",
      "pr_title": "pull_request.title",
      "pr_body": "pull_request.body"
    },
    "config": {
      "max_attempts": 3,
      "budget_per_trigger_usd": 5.00,
      "daily_limit": 20,
      "cooldown_seconds": 300
    }
  }'
```

### Trigger Configuration (Safety Limits)

| Setting | Default | Description |
|---------|---------|-------------|
| `max_attempts` | 3 | Max fires per (PR, trigger) combo |
| `budget_per_trigger_usd` | 5.00 | Cost limit per trigger fire |
| `daily_limit` | 20 | Max fires per day for this rule |
| `debounce_seconds` | 0 | Batch rapid events into one fire |
| `cooldown_seconds` | 300 | Min time between fires for same PR |

### Managing Triggers

```bash
# List triggers
uv run --package syn-cli syn triggers list

# Pause a trigger
uv run --package syn-cli syn triggers pause <trigger-id>

# Resume
uv run --package syn-cli syn triggers resume <trigger-id>

# Delete
uv run --package syn-cli syn triggers delete <trigger-id>
```

### Supported GitHub Events

| Event | Description | Common Conditions |
|-------|-------------|-------------------|
| `push` | Code pushed | `ref=refs/heads/main` |
| `pull_request` | PR opened/updated | `action=opened`, `base.ref=main` |
| `issues` | Issue created/updated | `action=opened`, `labels` |
| `issue_comment` | Comment on issue/PR | `action=created` |
| `workflow_run` | GitHub Actions completed | `action=completed` |

### Input Mapping

Maps webhook payload fields to workflow inputs using dot notation:

```json
{
  "pr_url": "pull_request.html_url",
  "repo_name": "repository.full_name",
  "branch": "pull_request.head.ref",
  "author": "sender.login"
}
```

### Trigger Events (Domain)

| Event | Description |
|-------|-------------|
| `TriggerRegisteredEvent` | New rule created |
| `TriggerFiredEvent` | Rule matched a webhook, execution started |
| `TriggerPausedEvent` | Rule temporarily disabled |
| `TriggerResumedEvent` | Rule re-enabled |
| `TriggerDeletedEvent` | Rule permanently removed |

## Common Scenarios

### "Set up automatic PR reviews"

1. Create a review workflow template with phases: analyze-diff, review-code, post-comments
2. Create a trigger rule on `pull_request` event with `action=opened` condition
3. Map `pull_request.html_url` to workflow input
4. Set `budget_per_trigger_usd: 2.00` and `cooldown_seconds: 300`

### "Track costs across my backend services"

1. Create an organization
2. Create a "Backend" system
3. Register repos and assign to system
4. View `SystemCost` read model via API: `GET /systems/<id>/cost`

### "Why didn't my trigger fire?"

1. Check trigger status — might be paused or deleted
2. Check `fire_count` — might have hit `max_attempts` or `daily_limit`
3. Check conditions — might not match the webhook payload
4. Check cooldown — another fire might have happened within `cooldown_seconds`
5. Check installation — GitHub App might be revoked
