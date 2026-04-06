---
name: github-automation
description: Set up GitHub App integration, create webhook trigger rules with safety limits, and automate Syntropic137 workflow execution from GitHub events
---

# GitHub Automation — Syntropic137

Use this knowledge when the user wants to set up GitHub App integration, create webhook trigger rules, or automate workflow execution based on GitHub events.

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

### Setup

GitHub App is configured during onboarding. Two paths:

**New App (manifest flow — recommended):**

**Source repo only:**
```bash
just onboard                              # Full setup wizard
just onboard-dev                          # Dev setup (includes GitHub App)
just setup-stage configure_github_app     # Re-run just the GitHub App stage
just github-reconfigure                   # Alias for the above
```

The manifest flow:
1. Opens browser to GitHub App creation page with pre-filled permissions
2. Polls for completion (~5 min timeout)
3. Downloads credentials: App ID, slug, PEM key, webhook secret
4. Stores in `.env` as `SYN_GITHUB_APP_ID`, `SYN_GITHUB_APP_NAME`, `SYN_GITHUB_WEBHOOK_SECRET`; PEM saved to `secrets/github-app-private-key.pem` (mounted as Docker secret)

**Existing App (manual):**

**Source repo only:**
```bash
just setup-stage configure_github_app
# Choose "existing" → provide App ID, name, PEM path, webhook secret
```

### Webhook Delivery

Webhooks need to reach the API. Two options depending on your environment:

| Method | Use Case | Setup |
|--------|----------|-------|
| **Cloudflare Tunnel** | Selfhost / production | Published path: configured during install. Source repo: `just onboard` configures tunnel + domain |
| **Smee.io proxy** | Local development only | `just onboard-dev` auto-creates channel (source repo only) |

**Selfhost / published path:** Cloudflare tunnels are the exclusive webhook delivery method. The tunnel routes GitHub webhooks through Cloudflare's network to your local API. Configure the tunnel's public hostname to point to `http://gateway:8081` in the Cloudflare Zero Trust dashboard.

**Development (source repo only):**
```bash
just dev-webhooks         # Start Smee proxy manually
just dev-webhooks-logs    # View proxy logs
```

### Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `SYN_GITHUB_APP_ID` | GitHub App ID |
| `SYN_GITHUB_APP_NAME` | GitHub App slug |
| `SYN_GITHUB_PRIVATE_KEY` | Base64-encoded PEM private key (legacy/dev fallback) |
| `SYN_GITHUB_APP_PRIVATE_KEY_FILE` | PEM file path (selfhost — set by compose via Docker secret) |
| `SYN_GITHUB_WEBHOOK_SECRET` | Webhook signature verification |
| `DEV__SMEE_URL` | Smee proxy URL (dev only) |

## Trigger Rules

Trigger rules automate workflow execution based on GitHub webhook events. A trigger says: *"When event X happens on repo Y matching conditions Z, start workflow W with inputs mapped from the webhook payload."*

### Creating Triggers

```bash
# Register a trigger rule via CLI
syn triggers register \
  --repo <repo-id> \
  --workflow <workflow-id> \
  --event pull_request \
  --condition action=opened \
  --condition base.ref=main \
  --max-fires 3 \
  --cooldown 300 \
  --budget 5.00
```

### Via API (Alternative)

```bash
curl -X POST http://localhost:8137/api/v1/triggers \
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
      "pr_body": "pull_request.body",
      "repository": "repository.full_name"
    },
    "config": {
      "max_attempts": 3,
      "budget_per_trigger_usd": 5.00,
      "daily_limit": 20,
      "cooldown_seconds": 300
    }
  }'
```

### Input Mapping

Maps webhook payload fields to workflow inputs using dot notation:

```json
{
  "pr_url": "pull_request.html_url",
  "repo_name": "repository.full_name",
  "branch": "pull_request.head.ref",
  "author": "sender.login",
  "repository": "repository.full_name"
}
```

The `repository` input is special — workflows with `{{repository}}` in their `repository.url` field will clone the triggering repo instead of a hardcoded one.

### Safety Limits (TriggerConfig)

| Setting | Default | Description |
|---------|---------|-------------|
| `max_attempts` | 3 | Max fires per (PR, trigger) combo |
| `budget_per_trigger_usd` | 5.00 | Cost limit per trigger fire |
| `daily_limit` | 20 | Max fires per day for this rule |
| `debounce_seconds` | 0 | Batch rapid events into one fire |
| `cooldown_seconds` | 300 | Min time between fires for same PR |

**Concurrency guard** — In addition to the configurable limits above, a built-in concurrency guard prevents catch-up storms after restart. If an execution is already RUNNING for the same `(trigger_id, pr_number)`, new events for that pair are blocked instead of firing duplicates.

These prevent runaway costs from chatty webhooks or infinite loops.

### Managing Triggers

```bash
# List all triggers
syn triggers list

# List triggers for a specific repo or by status
syn triggers list --repo <repo-id>
syn triggers list --status active

# Show trigger details
syn triggers show <trigger-id>

# View trigger fire history
syn triggers history <trigger-id>

# Pause a trigger (stops firing but keeps config)
syn triggers pause <trigger-id>

# Resume a paused trigger
syn triggers resume <trigger-id>

# Delete permanently
syn triggers delete <trigger-id>

# Emergency: disable all triggers
syn triggers disable-all

# Enable a preset trigger for a repo
syn triggers enable <preset> --repo <repo-id> --workflow <workflow-id>
```

### Via API (Alternative)

```bash
# List all triggers
curl -sf http://localhost:8137/api/v1/triggers

# Pause a trigger (stops firing but keeps config)
curl -sf -X POST http://localhost:8137/api/v1/triggers/<trigger-id>/pause

# Resume a paused trigger
curl -sf -X POST http://localhost:8137/api/v1/triggers/<trigger-id>/resume

# Delete permanently
curl -sf -X DELETE http://localhost:8137/api/v1/triggers/<trigger-id>
```

### Supported GitHub Events

| Event | Description | Common Conditions |
|-------|-------------|-------------------|
| `push` | Code pushed | `ref=refs/heads/main` |
| `pull_request` | PR opened/updated/closed | `action=opened`, `base.ref=main` |
| `issues` | Issue created/updated | `action=opened`, `labels` |
| `issue_comment` | Comment on issue/PR | `action=created` |
| `workflow_run` | GitHub Actions completed | `action=completed` |

### Trigger Conditions

Conditions use field/operator/value matching against the webhook payload:

```json
{"field": "action", "operator": "equals", "value": "opened"}
{"field": "base.ref", "operator": "equals", "value": "main"}
{"field": "pull_request.draft", "operator": "equals", "value": "false"}
```

### Domain Model

- **Aggregate**: `TriggerRuleAggregate`
- **Status**: `ACTIVE` | `PAUSED` | `DELETED`
- **Events**: `TriggerRegisteredEvent`, `TriggerFiredEvent`, `TriggerBlockedEvent`, `TriggerPausedEvent`, `TriggerResumedEvent`, `TriggerDeletedEvent`
- **Key state**: `name`, `event`, `conditions`, `repository`, `workflow_id`, `input_mapping`, `config`, `fire_count`

### Seeding Triggers

**Source repo only:**
```bash
just seed-triggers    # Seed preset triggers (self-healing, review-fix)
just seed-all         # Seed everything
```

## Common Scenarios

### "Set up automatic PR reviews"

1. Create a review workflow (e.g., the `github-pr` example workflow)
2. Create a trigger:
   ```bash
   syn triggers register \
     --repo <repo-id> \
     --workflow <workflow-id> \
     --event pull_request \
     --condition action=opened \
     --budget 2.00 \
     --cooldown 300
   ```
3. Install GitHub App on the target repo

### "Auto-fix issues when they're created"

1. Create an implementation workflow with issue-driven phases
2. Create a trigger:
   ```bash
   syn triggers register \
     --repo <repo-id> \
     --workflow <workflow-id> \
     --event issues \
     --condition action=opened \
     --budget 5.00 \
     --max-fires 10
   ```
3. Set conservative budget limits

### "Why didn't my trigger fire?"

1. **Check trigger history first** — blocked entries now show the exact guard and reason:
   ```bash
   syn triggers history <trigger-id>
   ```
   Blocked entries display `status: blocked` with `guard_name` and `block_reason`:
   - `concurrency` — execution already running for same trigger + PR
   - `max_attempts` — max fires reached for that PR
   - `cooldown` — too soon since last fire
   - `daily_limit` — daily fire cap reached
   - `idempotency` — duplicate event already processed
   - `conditions_not_met` — webhook payload didn't match conditions
2. Check trigger status — might be `PAUSED` or `DELETED`: `syn triggers show <trigger-id>`
3. Check installation — GitHub App might be revoked
4. Check webhook delivery — selfhost: check Cloudflare tunnel status; dev: `just dev-webhooks-logs` (source repo only) for Smee issues

### "How do I test triggers locally?"

1. Start the stack:
   - Published path: `cd ~/.syntropic137 && ./syn-ctl up`
   - **Source repo only:** `just dev` (includes webhook proxy)
2. Verify webhooks are being delivered:
   - Selfhost: check Cloudflare tunnel status in Zero Trust dashboard
   - **Source repo only:** `just dev-webhooks-logs`
3. Create a trigger pointing to a test workflow
4. Open a PR on the target repo — watch the execution start
5. **Source repo only:** Record webhooks for replay: `just dev-record-webhooks`
6. **Source repo only:** Replay later: `just replay-webhooks`
