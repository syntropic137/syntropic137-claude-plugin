---
model: opus
allowed-tools: Bash, Read, AskUserQuestion
---

# /syn-setup — Syntropic137 Self-Host Setup

You are setting up a self-hosted Syntropic137 instance. The user needs ONLY Docker — no source repo, no `uv`, no `just`, no `git`. Everything runs from `~/.syntropic137/` using pre-built container images pulled from GitHub Container Registry.

Your job: walk the user through setup conversationally, running bash commands and asking questions as needed. Stay in the loop for every step — never hand off to an external wizard.

**Working directory:** `~/.syntropic137/`
**Compose file:** `docker-compose.syntropic137.yaml`
**Port:** `8137`
**Release assets URL:** `https://github.com/syntropic137/syntropic137/releases/latest`

---

## Phase 1 — Docker Detection

Check that Docker is installed and Compose meets the minimum version.

```bash
docker --version 2>/dev/null
docker compose version 2>/dev/null
```

- If `docker` is not found: tell the user to install Docker Desktop (https://docs.docker.com/get-docker/) and re-run `/syn-setup`. **Stop here.**
- If `docker compose` is not found or the version is below 2.20: tell the user to update Docker Desktop (Compose V2 ships with it). **Stop here.**
- If Docker is installed but the daemon is not running (`docker info` fails): tell the user to start Docker Desktop. **Stop here.**

Parse the Compose version from `docker compose version` output (e.g., `Docker Compose version v2.32.4`). Extract the major.minor and compare against 2.20.

---

## Phase 2 — Re-run Detection

Check if `~/.syntropic137/` already exists.

```bash
test -d "$HOME/.syntropic137" && echo "EXISTS" || echo "FRESH"
```

**If FRESH:** skip to Phase 3.

**If EXISTS:** audit what is already configured. Run these checks:

```bash
# .env present?
test -f "$HOME/.syntropic137/.env" && echo "env:yes" || echo "env:no"

# Secrets present?
for f in db-password.secret redis-password.secret minio-password.secret; do
  test -f "$HOME/.syntropic137/secrets/$f" && echo "secret:$f:yes" || echo "secret:$f:no"
done

# API key configured?
grep -q 'ANTHROPIC_API_KEY=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "apikey:yes" || echo "apikey:no"

# GitHub App configured?
grep -q 'SYN_GITHUB_APP_ID=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "github:yes" || echo "github:no"

# Cloudflare configured?
grep -q 'CLOUDFLARE_TUNNEL_TOKEN=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "cloudflare:yes" || echo "cloudflare:no"

# 1Password backed up?
grep -q 'SYN_1PASSWORD_BACKUP=true' "$HOME/.syntropic137/.env" 2>/dev/null && echo "1password:yes" || echo "1password:no"

# Containers running?
docker compose -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo "containers:none"

# API healthy?
curl -sf http://localhost:8137/health 2>/dev/null || echo "api:unreachable"
```

Present a status matrix to the user:

```
Syntropic137 — Existing Installation Detected
═══════════════════════════════════════════════
 Component              Status
───────────────────────────────────────────────
 .env file              ✓ / ✗
 Secrets                ✓ / ✗
 API key                ✓ / ✗
 GitHub App             ✓ / ✗
 Cloudflare tunnel      ✓ / ✗
 1Password backup       ✓ / ✗
 Containers             Running / Stopped / Not pulled
 API health             Healthy / Unreachable
═══════════════════════════════════════════════
```

Then ask the user:

> What would you like to do?
> 1. Add missing features (keeps existing config)
> 2. Update to the latest release
> 3. Reconfigure from scratch (backs up current .env)

- **Option 1:** Identify which phases are incomplete and skip to the first missing one. For example, if secrets and API key exist but GitHub App is not configured, skip to Phase 7.
- **Option 2:** Run `npx @syntropic137/setup update` to pull the latest compose file and images and restart. Preserve `.env` and secrets.
- **Option 3:** Back up `.env` to `.env.backup.<timestamp>`, then proceed from Phase 3 as a fresh install.

---

## Phase 3 — Create Working Directory + Download Release Assets

```bash
mkdir -p "$HOME/.syntropic137/secrets"
```

Download release assets from the latest GitHub release. Use the GitHub API to resolve the latest tag, then download each asset:

```bash
# Get latest release tag
LATEST_TAG=$(curl -sL https://api.github.com/repos/syntropic137/syntropic137/releases/latest | grep '"tag_name"' | sed 's/.*"tag_name": "\(.*\)".*/\1/')

# Download release assets
RELEASE_BASE="https://github.com/syntropic137/syntropic137/releases/download/${LATEST_TAG}"

curl -sL "${RELEASE_BASE}/docker-compose.syntropic137.yaml" -o "$HOME/.syntropic137/docker-compose.syntropic137.yaml"
curl -sL "${RELEASE_BASE}/selfhost.env.example" -o "$HOME/.syntropic137/.env"
curl -sL "${RELEASE_BASE}/selfhost-entrypoint.sh" -o "$HOME/.syntropic137/selfhost-entrypoint.sh"

chmod +x "$HOME/.syntropic137/selfhost-entrypoint.sh"
```

Verify all files were downloaded (non-empty):

```bash
for f in docker-compose.syntropic137.yaml .env selfhost-entrypoint.sh; do
  test -s "$HOME/.syntropic137/$f" && echo "$f: OK" || echo "$f: FAILED"
done
```

If any file failed to download, show the error and suggest the user check their internet connection or that the release exists. **Stop here** if the compose file failed — the other files are recoverable but the compose file is required.

Write the version tag to a metadata file for later use:

```bash
echo "$LATEST_TAG" > "$HOME/.syntropic137/.version"
```

---

## Phase 4 — Feature Selection

Present an executive summary explaining what is required vs optional. Use this exact structure in your message to the user:

---

**Syntropic137 Self-Host Setup**

This sets up your self-hosted AI agent orchestration platform. Here is what is involved:

**REQUIRED (handled automatically):**
- Docker + Compose -- already confirmed
- Infrastructure secrets -- database, Redis, MinIO passwords (auto-generated)
- LLM API key -- you will be prompted (agents need this to run)
- Pull and start -- pre-built images on localhost:8137

**REQUIRED:**

**GitHub App** -- *required for agents to interact with GitHub*
Creates a private bot for your GitHub repos. Enables pushing code, creating PRs, code review, and webhook-triggered workflows. Setup: ~2 min via one-click manifest flow.
Requires: GitHub account (free).

**OPTIONAL FEATURES:**

**[1] Cloudflare Tunnel** -- *recommended*
Gives your instance a public URL for GitHub webhooks. Required for auto-triggering workflows on push/PR. Without this, manual runs only and dashboard on localhost only.
Requires: Cloudflare account + domain ($10-15/yr if buying new). Setup: ~5 min.

**[2] 1Password** -- *recommended*
Backs up all secrets to 1Password. Restore on a new machine in minutes.
Requires: 1Password app + `op` CLI (any plan -- personal works). Setup: ~1 min.

---

Ask the user:

> Select optional features to set up: [1,2 / all / none] (default: all)

Parse the response:
- `all` or empty/Enter: enable both optional features
- `none`: skip optional features (GitHub App still set up)
- `1` or `2` or `1,2`: enable the listed features

Store the selections for use in later phases. Optional features can be added later by running `/syn-setup` again.

---

## Phase 5 — API Key

Ask the user for their Anthropic API key:

> Agents need an LLM provider to run. Please provide your Anthropic API key.
>
> You can get one at https://console.anthropic.com/settings/keys
>
> Alternatively, if you use Claude Code with OAuth, you can set `CLAUDE_CODE_OAUTH_TOKEN` instead.
>
> Paste your ANTHROPIC_API_KEY:

Write the key to `.env`:

```bash
# Use sed to replace the placeholder in .env (from the example file)
sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=${API_KEY}|" "$HOME/.syntropic137/.env"
rm -f "$HOME/.syntropic137/.env.bak"
```

If the user provides an OAuth token instead, write `CLAUDE_CODE_OAUTH_TOKEN` to `.env`.

**Do NOT echo the key back to the user or include it in any output.**

---

## Phase 6 — Generate Secrets

Generate infrastructure secrets automatically. No user input needed.

```bash
openssl rand -hex 32 > "$HOME/.syntropic137/secrets/db-password.secret"
openssl rand -hex 32 > "$HOME/.syntropic137/secrets/redis-password.secret"
openssl rand -hex 32 > "$HOME/.syntropic137/secrets/minio-password.secret"

chmod 600 "$HOME/.syntropic137/secrets/"*.secret
```

Tell the user:

> Infrastructure secrets generated and stored in `~/.syntropic137/secrets/` with restricted permissions (600).

---

## Phase 7 — GitHub App

**Always run this phase — GitHub App is required for agents to interact with GitHub.**

Tell the user:

> Setting up your GitHub App. This creates a private bot that connects to your repos.
>
> I will open the GitHub App manifest flow in your browser. Click "Create GitHub App" on the page -- it is a one-click setup that pre-fills all the right permissions and webhook URLs.

Construct and open the manifest flow URL:

```bash
open "https://github.com/settings/apps/new?manifest_url=https://github.com/syntropic137/syntropic137/blob/main/infra/github-app-manifest.json" 2>/dev/null || \
  echo "Please open this URL in your browser: https://github.com/settings/apps/new"
```

Then ask the user for the details:

> After creating the app, GitHub shows you the app settings page. I need a few values from there:
>
> 1. **App ID** (shown at the top of the General settings page)
> 2. **App name** (the name you chose or was generated)
> 3. **Webhook secret** (if you set one -- or I can generate one)
> 4. **Private key** -- click "Generate a private key" on the settings page. It downloads a `.pem` file. Tell me the path to that file (e.g., `~/Downloads/my-app.2026-03-26.private-key.pem`).

Collect each value from the user. For the webhook secret, if the user does not have one, generate it:

```bash
openssl rand -hex 20
```

For the private key, copy it to the secrets directory:

```bash
cp "<user-provided-path>" "$HOME/.syntropic137/secrets/github-app-private-key.pem"
chmod 600 "$HOME/.syntropic137/secrets/github-app-private-key.pem"
```

Write all GitHub App values to `.env`:

```bash
sed -i.bak "s|^SYN_GITHUB_APP_ID=.*|SYN_GITHUB_APP_ID=${APP_ID}|" "$HOME/.syntropic137/.env"
sed -i.bak "s|^SYN_GITHUB_APP_NAME=.*|SYN_GITHUB_APP_NAME=${APP_NAME}|" "$HOME/.syntropic137/.env"
sed -i.bak "s|^SYN_GITHUB_WEBHOOK_SECRET=.*|SYN_GITHUB_WEBHOOK_SECRET=${WEBHOOK_SECRET}|" "$HOME/.syntropic137/.env"
sed -i.bak "s|^SYN_GITHUB_APP_PRIVATE_KEY_PATH=.*|SYN_GITHUB_APP_PRIVATE_KEY_PATH=/run/secrets/github-app-private-key.pem|" "$HOME/.syntropic137/.env"
rm -f "$HOME/.syntropic137/.env.bak"
```

If any `.env` key does not already exist as a placeholder, append it instead of using sed.

---

## Phase 8 — Cloudflare Tunnel (if selected)

**Only run this phase if the user selected optional feature [1].**

Tell the user:

> Setting up a Cloudflare tunnel to give your instance a public URL.
>
> 1. Open the Cloudflare Zero Trust dashboard:
>    https://dash.cloudflare.com/?to=/:account/tunnels
>
> 2. Click "Create a tunnel" and choose "Cloudflared"
>
> 3. Name it something like `syntropic137`
>
> 4. In the "Route tunnel" step, configure:
>    - **Public hostname:** choose your subdomain (e.g., `syn.yourdomain.com`)
>    - **Service:** `http://localhost:8137`
>
> 5. On the "Install and run connectors" step, copy the tunnel token (the long string after `--token`)

Ask the user:

> Paste your Cloudflare tunnel token:

Then ask:

> What is the public hostname you configured? (e.g., `syn.yourdomain.com`)

Write both values to `.env`:

```bash
sed -i.bak "s|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=${TUNNEL_TOKEN}|" "$HOME/.syntropic137/.env"
sed -i.bak "s|^SYN_PUBLIC_HOSTNAME=.*|SYN_PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME}|" "$HOME/.syntropic137/.env"
rm -f "$HOME/.syntropic137/.env.bak"
```

If any `.env` key does not already exist as a placeholder, append it instead of using sed.

---

## Phase 9 — 1Password Backup (if selected)

**Only run this phase if the user selected optional feature [2].**

Check if the `op` CLI is available and signed in:

```bash
op whoami 2>/dev/null
```

- If `op` is not found: tell the user to install it from https://developer.1password.com/docs/cli/get-started/ and re-run `/syn-setup` to add 1Password later. **Skip this phase.**
- If `op whoami` fails: tell the user to sign in with `op signin` and re-run `/syn-setup` to add 1Password later. **Skip this phase.**

Create the vault if it does not exist:

```bash
op vault get syntropic137 >/dev/null 2>&1 || op vault create syntropic137
```

Build a JSON template with all secrets and pipe it to `op` via stdin. **NEVER pass secret values as CLI arguments — they are visible in `ps aux`.**

```bash
cat <<'TEMPLATE_EOF' | python3 -c "
import json, sys, os

secrets_dir = os.path.expanduser('~/.syntropic137/secrets')
env_file = os.path.expanduser('~/.syntropic137/.env')

# Read secrets from files
def read_secret(name):
    path = os.path.join(secrets_dir, name)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return ''

# Read specific env values
env_vals = {}
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env_vals[k] = v

fields = []
fields.append({'label': 'db-password', 'value': read_secret('db-password.secret'), 'type': 'CONCEALED'})
fields.append({'label': 'redis-password', 'value': read_secret('redis-password.secret'), 'type': 'CONCEALED'})
fields.append({'label': 'minio-password', 'value': read_secret('minio-password.secret'), 'type': 'CONCEALED'})

for key in ['ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN', 'SYN_GITHUB_APP_ID', 'SYN_GITHUB_APP_NAME', 'SYN_GITHUB_WEBHOOK_SECRET', 'CLOUDFLARE_TUNNEL_TOKEN', 'SYN_PUBLIC_HOSTNAME']:
    if env_vals.get(key):
        fields.append({'label': key, 'value': env_vals[key], 'type': 'CONCEALED'})

# Read GitHub App private key if it exists
pem_path = os.path.join(secrets_dir, 'github-app-private-key.pem')
if os.path.exists(pem_path):
    with open(pem_path) as f:
        fields.append({'label': 'github-app-private-key', 'value': f.read().strip(), 'type': 'CONCEALED'})

print(json.dumps(fields))
" | op item create --category=login \
    --title="syntropic137-config" \
    --vault="syntropic137" \
    --template=-
```

If the item already exists, update it instead (or delete and recreate).

On success, mark in `.env`:

```bash
echo "SYN_1PASSWORD_BACKUP=true" >> "$HOME/.syntropic137/.env"
```

Tell the user:

> All secrets backed up to 1Password vault "syntropic137", item "syntropic137-config". You can restore on a new machine by re-running `npx @syntropic137/setup init`.

---

## Phase 10 — Pull and Start

Pull all container images and start the stack:

```bash
cd "$HOME/.syntropic137" && docker compose -f docker-compose.syntropic137.yaml pull
```

Show progress to the user. If the pull fails, check internet connectivity and whether the images exist on GHCR.

Then start the stack:

```bash
cd "$HOME/.syntropic137" && docker compose -f docker-compose.syntropic137.yaml up -d
```

If there are errors (port conflicts, permission issues), diagnose and report to the user.

---

## Phase 11 — Health Check + Post-Setup Guidance

Poll the health endpoint until it responds (timeout after 60 seconds):

```bash
TRIES=0
while [ $TRIES -lt 30 ]; do
  if curl -sf http://localhost:8137/health >/dev/null 2>&1; then
    echo "HEALTHY"
    break
  fi
  sleep 2
  TRIES=$((TRIES + 1))
done

if [ $TRIES -ge 30 ]; then
  echo "TIMEOUT"
fi
```

**If HEALTHY:** read the version from the health endpoint:

```bash
curl -sf http://localhost:8137/health
```

Then check if a public hostname is configured:

```bash
_hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
```

Present the post-setup summary to the user. If a public hostname is configured, show both local and public URLs:

```
Syntropic137 is running!
═══════════════════════════════════════════════════

 Dashboard:   http://localhost:8137 (local)
 Dashboard:   https://<hostname> (public — via Cloudflare tunnel)
 API Docs:    http://localhost:8137/docs (local)
 API Docs:    https://<hostname>/docs (public)
 Version:     <version from health endpoint>

 WHAT'S NEXT:

 1. Open the dashboard -- see your platform overview
 2. Create your first workflow:
    "Create a workflow that reviews PRs on my repo"
 3. Trigger a manual run:
    /syn-workflow run <workflow-id> --task "Hello world"
 4. Set up automatic PR triggers:
    "Set up triggers for my-org/my-repo"

 Run /syn-setup again anytime to add features or update.
═══════════════════════════════════════════════════
```

If no public hostname is configured, show only the local URLs (without the "(local)" suffix):

```
Syntropic137 is running!
═══════════════════════════════════════════════════

 Dashboard:   http://localhost:8137
 API Docs:    http://localhost:8137/docs
 Version:     <version from health endpoint>
 ...
```

**If TIMEOUT:** check container status and logs to diagnose:

```bash
cd "$HOME/.syntropic137" && docker compose -f docker-compose.syntropic137.yaml ps
cd "$HOME/.syntropic137" && docker compose -f docker-compose.syntropic137.yaml logs --tail=50
```

Present the findings and suggest remediation.

---

## Tone and Style

- Be conversational, not robotic. Explain *why* at each step.
- When something is auto-generated (secrets, webhook secret), tell the user it is handled -- do not dump raw output.
- When asking for input, give context: what is it, where to find it, why it is needed.
- If something fails, diagnose it -- do not just print the error. Check logs, suggest fixes.
- Keep the flow moving. Do not pause unnecessarily between automated phases (5, 6, 10).
- Group automated phases together and report results, then pause for interactive phases (7, 8, 9).
