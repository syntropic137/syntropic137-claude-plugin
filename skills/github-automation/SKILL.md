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
4. Stores in `.env` as `SYN_GITHUB_APP_ID`, `SYN_GITHUB_APP_NAME`, `SYN_GITHUB_PRIVATE_KEY`, `SYN_GITHUB_WEBHOOK_SECRET`

**Existing App (manual):**
```bash
just setup-stage configure_github_app
# Choose "existing" → provide App ID, name, PEM path, webhook secret
```

### Webhook Delivery

Webhooks need to reach the API. Two options:

| Method | Use Case | Setup |
|--------|----------|-------|
| **Cloudflare Tunnel** | Production/selfhost | `just onboard` configures tunnel + domain |
| **Smee.io proxy** | Development only | `just onboard-dev` auto-creates channel |

Dev webhook proxy:
```bash
just dev-webhooks         # Start Smee proxy manually
just dev-webhooks-logs    # View proxy logs
```

### Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `SYN_GITHUB_APP_ID` | GitHub App ID |
| `SYN_GITHUB_APP_NAME` | GitHub App slug |
| `SYN_GITHUB_PRIVATE_KEY` | Base64-encoded PEM private key |
| `SYN_GITHUB_WEBHOOK_SECRET` | Webhook signature verification |
| `DEV__SMEE_URL` | Smee proxy URL (dev only) |

## Trigger Rules

Trigger rules automate workflow execution based on GitHub webhook events. A trigger says: *"When event X happens on repo Y matching conditions Z, start workflow W with inputs mapped from the webhook payload."*

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

These prevent runaway costs from chatty webhooks or infinite loops.

### Managing Triggers

```bash
# List all triggers
uv run --package syn-cli syn triggers list

# Pause a trigger (stops firing but keeps config)
uv run --package syn-cli syn triggers pause <trigger-id>

# Resume a paused trigger
uv run --package syn-cli syn triggers resume <trigger-id>

# Delete permanently
uv run --package syn-cli syn triggers delete <trigger-id>
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
- **Events**: `TriggerRegisteredEvent`, `TriggerFiredEvent`, `TriggerPausedEvent`, `TriggerResumedEvent`, `TriggerDeletedEvent`
- **Key state**: `name`, `event`, `conditions`, `repository`, `workflow_id`, `input_mapping`, `config`, `fire_count`

### Seeding Triggers

```bash
just seed-triggers    # Seed preset triggers (self-healing, review-fix)
just seed-all         # Seed everything
```

## Common Scenarios

### "Set up automatic PR reviews"

1. Create a review workflow (e.g., the `github-pr` example workflow)
2. Create a trigger:
   - Event: `pull_request`
   - Condition: `action=opened`
   - Input mapping: `pr_url` → `pull_request.html_url`, `repository` → `repository.full_name`
   - Budget: `$2.00` per trigger, cooldown 5 min
3. Install GitHub App on the target repo

### "Auto-fix issues when they're created"

1. Create an implementation workflow with issue-driven phases
2. Create a trigger:
   - Event: `issues`
   - Condition: `action=opened`
   - Input mapping: `issue_url` → `issue.html_url`, `repository` → `repository.full_name`
3. Set conservative budget limits (`$5.00`, daily limit 10)

### "Why didn't my trigger fire?"

1. Check trigger status — might be `PAUSED` or `DELETED`
2. Check `fire_count` vs `max_attempts` — might be exhausted for that PR
3. Check `daily_limit` — might have hit the daily cap
4. Check conditions — might not match the webhook payload
5. Check `cooldown_seconds` — too recent since last fire
6. Check installation — GitHub App might be revoked
7. Check webhook delivery — `just dev-webhooks-logs` for Smee issues

### "How do I test triggers locally?"

1. Start the dev stack: `just dev` (includes webhook proxy)
2. Verify webhooks are being delivered: `just dev-webhooks-logs`
3. Create a trigger pointing to a test workflow
4. Open a PR on the target repo — watch the execution start
5. Record webhooks for replay: `just dev-record-webhooks`
6. Replay later: `just replay-webhooks`
