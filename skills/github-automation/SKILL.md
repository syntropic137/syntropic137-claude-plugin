---
name: github-automation
description: Set up GitHub App integration, create webhook trigger rules with safety limits, and automate Syntropic137 workflow execution from GitHub events
---

# GitHub Automation: Syntropic137

When you want workflows to run automatically on GitHub events (a PR opened, an issue created, a commit pushed), trigger rules are how you wire that up. **NEVER create trigger rules without setting safety limits.** Chatty webhooks, PR bots, and CI loops can fire your triggers hundreds of times per day without `daily_limit`, `cooldown_seconds`, and `max_attempts` in place.

## When to Use This Skill

Use this when you are: setting up the GitHub App for the first time, creating trigger rules to automate workflow execution, debugging why a trigger didn't fire, or managing existing trigger rules.

Not needed for running workflows manually; use execution-control for that. Not needed for managing trigger rules interactively; use `/syn-triggers` for that.

## The Trigger Rule Pattern

A trigger rule says: *"When event X occurs on repo Y matching conditions Z, start workflow W with inputs mapped from the webhook payload."*

```
GitHub Event (e.g., pull_request opened)
  → Webhook → Cloudflare Tunnel → API gateway
  → TriggerRuleAggregate evaluates conditions
  → Safety guards check: concurrency, max_attempts, cooldown, daily_limit
  → If all pass → WorkflowExecutionStarted
  → input_mapping extracts values from webhook payload → workflow inputs
```

The aggregate is the decision-maker. Safety guards run before any execution starts.

## Safety Limits: Set These Every Time

```json
{
  "max_attempts": 3,
  "budget_per_trigger_usd": 5.00,
  "daily_limit": 20,
  "cooldown_seconds": 300
}
```

| Limit | What It Prevents |
|-------|-----------------|
| `max_attempts` | Re-firing on the same PR more than N times |
| `budget_per_trigger_usd` | A single trigger fire spending more than budget |
| `daily_limit` | The rule firing more than N times total per day |
| `cooldown_seconds` | Rapid re-fires on the same PR within the cooldown window |

The built-in **concurrency guard** is automatic: if an execution is already `RUNNING` for the same `(trigger_id, pr_number)`, new events for that pair are blocked. This prevents catch-up storms after a restart.

## GitHub App Setup

The GitHub App provides: repository access for workspace cloning, webhook delivery, and status reporting back to PRs.

**First-time setup (recommended, using manifest flow):**
```bash
npx @syntropic137/setup github-app
```
This opens a browser to GitHub App creation with pre-filled permissions, polls for completion, and saves the App ID, PEM key, and webhook secret to your config.

**Source repo developers:**
```bash
just onboard-dev              # includes GitHub App + webhook proxy (Smee.io for local)
just setup-stage configure_github_app   # re-run just the App stage
```

**Webhook delivery:** Self-hosters use Cloudflare tunnel (route to `http://gateway:8081`). Local dev uses Smee.io (`just dev-webhooks`).

## Creating a Trigger Rule: 3 Steps

**Step 1:** Ensure the GitHub App is installed on the target repo and the workflow you want to trigger is registered (`syn workflow list`).

**Step 2:** Register the trigger with safety limits:

```bash
syn triggers register \
  --name "pr-review" \
  --event pull_request \
  --repository owner/repo \
  --workflow <workflow-id> \
  --condition action=opened \
  --condition base.ref=main \
  --max-fires 3 \
  --budget 5.00 \
  --cooldown 300
```

**Step 3:** Verify with `syn triggers list --repository owner/repo`; the trigger should show as `ACTIVE`.

## Input Mapping

Map webhook payload fields to workflow inputs using dot notation:

```json
{
  "pr_url": "pull_request.html_url",
  "repository": "repository.full_name",
  "branch": "pull_request.head.ref",
  "author": "sender.login"
}
```

The `repository` input is special: if your workflow template uses `{{repository}}` in its `repository.url`, it will clone the triggering repo automatically.

## Debugging a Trigger That Didn't Fire

**First: check trigger history**: blocked entries show exactly which guard blocked the event and why:

```bash
syn triggers history <trigger-id>
```

Guard names and what they mean:
- `concurrency`: execution already running for this trigger + PR
- `max_attempts`: PR hit the per-trigger fire limit
- `cooldown`: fired too recently for this PR
- `daily_limit`: daily cap reached for this rule
- `conditions_not_met`: webhook payload didn't match conditions

If no history entries exist, the webhook may not have arrived. Check: `syn triggers show <id>` for status, then verify the GitHub App installation and webhook delivery (Cloudflare tunnel / Smee).

## Supported Events

`push`, `pull_request`, `issues`, `issue_comment`, `workflow_run`, `check_run`

Conditions use field/operator/value matching: `{"field": "action", "operator": "equals", "value": "opened"}`. Dot notation traverses the payload: `pull_request.draft`, `repository.full_name`, `sender.login`.

## Managing Triggers

```bash
syn triggers list
syn triggers pause <id> --reason "investigating"
syn triggers resume <id>
syn triggers disable-all          # emergency stop
syn triggers delete <id>          # permanent
```

## Escalation Point

If triggers fire repeatedly without producing useful output (agent runs complete but don't act on the PR), the problem is likely in the workflow template's `input_mapping`; the workflow isn't receiving the right inputs from the payload. Check `syn triggers history <id>` for what was actually passed as inputs, then compare to what the workflow expects.

## Integration

Set up GitHub App first, then create workflows with workflow-management, then wire triggers here. Monitor trigger-fired executions with execution-control and observability. Use `/syn-triggers` for interactive trigger management from Claude Code.
