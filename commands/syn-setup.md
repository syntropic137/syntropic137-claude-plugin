---
model: opus
allowed-tools: Bash, Read
---

# /syn-setup — Syntropic137 Self-Host Setup

You are helping the user set up a self-hosted Syntropic137 instance. The entire setup flow is handled by the `@syntropic137/setup` npx package — your job is just to check prerequisites and hand off to it.

---

## Step 1 — Explain

Tell the user:

> **Setting up Syntropic137 via the setup CLI.**
>
> This will walk you through the full self-host setup interactively — Docker checks, secrets, GitHub App, Cloudflare tunnel, and starting the stack. Everything is handled by the setup tool.

---

## Step 2 — Check Node.js

```bash
node --version 2>/dev/null
```

- If `node` is not found or the major version is below 18: tell the user to install Node.js 18+ and re-run `/syn-setup`. Point them to https://nodejs.org/ . **Stop here.**
- If Node.js 18+ is present: continue.

---

## Step 3 — Hand Off to the User

The setup CLI is fully interactive (arrow-key menus, masked password prompts, browser-based OAuth). It **cannot** be driven by Claude — the user must run it in their own terminal.

Determine whether this is a fresh install or an existing installation:

```bash
test -d "$HOME/.syntropic137" && echo "EXISTS" || echo "FRESH"
```

**If FRESH**, tell the user to run this in their terminal:

```
npx @syntropic137/setup init
```

**If EXISTS**, tell the user to run this in their terminal:

```
npx @syntropic137/setup
```

Tell the user:

> Run that command in a separate terminal. It's fully interactive — it'll walk you through Docker checks, secrets, GitHub App creation, and starting the stack. Come back here when it's done and I can help verify everything is working.

**Do NOT run the npx command yourself.** Wait for the user to come back and confirm completion.

---

## Step 4 — Verify (after user returns)

Once the user confirms the setup CLI finished, verify the stack is healthy:

```bash
docker compose -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ps --format "table {{.Name}}\t{{.Status}}"
```

```bash
curl -sf http://127.0.0.1:8137/health
```

- If all containers are running and the health endpoint returns OK: tell the user setup is complete and suggest next steps (open the dashboard at http://localhost:8137, try `/syn-status`, create a workflow).
- If containers are down or health fails: check logs with `docker compose -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" logs --tail=30` and help troubleshoot.

---

## Remote Access

To enable GitHub webhooks and full event coverage (60+ event types vs 17 with polling):

```bash
npx @syntropic137/setup tunnel
```
