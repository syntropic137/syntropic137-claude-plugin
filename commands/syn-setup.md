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
grep -q '^ANTHROPIC_API_KEY=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "apikey:yes" || echo "apikey:no"

# GitHub App configured?
grep -q '^SYN_GITHUB_APP_ID=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "github:yes" || echo "github:no"

# GitHub App PEM present?
test -s "$HOME/.syntropic137/secrets/github-app-private-key.pem" && echo "pem:yes" || echo "pem:no"

# Cloudflare configured?
grep -q '^CLOUDFLARE_TUNNEL_TOKEN=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "cloudflare:yes" || echo "cloudflare:no"

# 1Password backed up?
grep -q '^SYN_1PASSWORD_BACKUP=true' "$HOME/.syntropic137/.env" 2>/dev/null && echo "1password:yes" || echo "1password:no"

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
 GitHub App PEM         ✓ / ✗
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
- **Option 2:** Download the latest compose file and `syn-ctl`, run `docker compose pull`, restart. Preserve `.env` and secrets.
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
curl -sL "${RELEASE_BASE}/syn-ctl" -o "$HOME/.syntropic137/syn-ctl"
curl -sL "${RELEASE_BASE}/selfhost-entrypoint.sh" -o "$HOME/.syntropic137/selfhost-entrypoint.sh"

chmod +x "$HOME/.syntropic137/syn-ctl"
chmod +x "$HOME/.syntropic137/selfhost-entrypoint.sh"
```

Verify all files were downloaded correctly. Check both that files are non-empty AND that they don't contain GitHub 404 responses (which are non-empty HTML/text that passes a simple size check):

```bash
for f in docker-compose.syntropic137.yaml .env syn-ctl selfhost-entrypoint.sh; do
  if [ ! -s "$HOME/.syntropic137/$f" ]; then
    echo "$f: FAILED (empty or missing)"
  elif head -1 "$HOME/.syntropic137/$f" | grep -Eqi 'not found|404|<!DOCTYPE'; then
    echo "$f: FAILED (got error page instead of file content)"
  else
    echo "$f: OK"
  fi
done
```

If any file failed to download, show the error and suggest the user check their internet connection or that the release exists at `${RELEASE_BASE}`. Common cause: the release tag exists but the assets haven't been uploaded yet.

**Stop here** if the compose file or `.env` failed — both are required. The `.env` template must contain actual configuration (look for `APP_ENVIRONMENT` as a sanity check):

```bash
grep -q '^APP_ENVIRONMENT=' "$HOME/.syntropic137/.env" 2>/dev/null && echo "env-template:valid" || echo "env-template:invalid"
```

If the `.env` is invalid, the setup cannot proceed — secrets would be written to a garbage file.

Write the version tag to a metadata file for later use:

```bash
echo "$LATEST_TAG" > "$HOME/.syntropic137/.version"
```

Create a helper script for setting secrets programmatically (used for headless/scripted installs outside Claude Code — the primary setup flow uses the editor instead):

```bash
cat > "$HOME/.syntropic137/set-secret.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="$HOME/.syntropic137/.env"

usage() {
  echo "Usage: set-secret.sh <KEY_NAME>"
  echo ""
  echo "Prompts for a value and writes it to .env securely."
  echo "The value never appears in process args or shell history."
  echo ""
  echo "Examples:"
  echo "  set-secret.sh ANTHROPIC_API_KEY"
  echo "  set-secret.sh CLAUDE_CODE_OAUTH_TOKEN"
  echo "  set-secret.sh CLOUDFLARE_TUNNEL_TOKEN"
  exit 1
}

[ -z "${1:-}" ] && usage

KEY_NAME="$1"

# Validate key name (alphanumeric + underscore only)
if ! echo "$KEY_NAME" | grep -qE '^[A-Z0-9_]+$'; then
  echo "Error: invalid key name. Use only A-Z, 0-9, underscore." >&2
  exit 1
fi

read -rsp "${KEY_NAME}: " _val && printf '\n'

if [ -z "$_val" ]; then
  echo "Error: empty value." >&2
  exit 1
fi

# Reject values containing newlines
if echo "$_val" | grep -q $'\n'; then
  echo "Error: value must not contain newlines." >&2
  unset _val
  exit 1
fi

# Cloudflare: extract eyJ... token if user pasted full install command
if [ "$KEY_NAME" = "CLOUDFLARE_TUNNEL_TOKEN" ]; then
  _extracted=$(echo "$_val" | grep -oE 'eyJ[A-Za-z0-9_.=-]+' | tail -1)
  if [ -n "$_extracted" ]; then
    _val="$_extracted"
  fi
  unset _extracted
fi

# Rewrite .env via Python so the secret never appears in process args
# (sed would expose it via /proc/pid/cmdline or ps)
python3 -c "
import sys, os

key = sys.argv[1]
val = sys.stdin.readline().rstrip('\n')
env_file = os.path.expanduser('~/.syntropic137/.env')

lines = []
found = False
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith(key + '='):
                lines.append(key + '=' + val + '\n')
                found = True
            else:
                lines.append(line)

if not found:
    lines.append(key + '=' + val + '\n')

with open(env_file, 'w') as f:
    f.writelines(lines)

os.chmod(env_file, 0o600)
" "$KEY_NAME" <<< "$_val"

unset _val
echo "✓ ${KEY_NAME} saved to .env"
SCRIPT_EOF
chmod +x "$HOME/.syntropic137/set-secret.sh"
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
Creates a private bot for your GitHub repos. Enables pushing code, creating PRs, code review, and webhook-triggered workflows. Setup: ~3 min (manual form).
Requires: GitHub account (free).
*Note: if you select Cloudflare Tunnel, that will be configured first — you need the public URL before filling in the GitHub App webhook field.*

**OPTIONAL FEATURES:**

**[1] Cloudflare Tunnel** -- *recommended*
Provides a stable public endpoint for your instance. Enables two things: (1) **GitHub webhook delivery** — required for auto-triggering workflows on push/PR/issue events, and (2) **remote access** — reach your dashboard and API from anywhere, not just localhost. Without this, agents still work (push code, create PRs, review) but must be triggered manually, and the dashboard is localhost-only.
**Set up before GitHub App** — the tunnel hostname is used as the webhook URL.
Requires: Cloudflare account + domain (~$15/yr if buying new). Setup: ~5 min.

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

## Editor Selection

Before Phase 5, detect the OS to decide which editor command to show the user:

- **macOS (`Darwin`):** Use `open -t` — opens in the user's default GUI text editor (VS Code, TextEdit, Sublime, etc.)
- **Linux:** Use `$EDITOR` if set, otherwise `nano`. Include terminal editor hints (nano: `Ctrl+O`, `Ctrl+X`).

```bash
uname
```

Use the result to show the correct command in Phase 5 and 7 instructions below.

---

## Security Note (display before Phase 5)

Before collecting any credentials, reassure the user:

> **A note on security:** The next few phases involve API keys, tokens, and a private key. I will never ask you to paste a secret into this chat — that would store it in conversation history.
>
> Instead, I will open your `.env` config file in a text editor. You paste your secrets directly into the file, save, and close. The values stay between you and your filesystem — I only check whether a key was set (not what the value is).
>
> **How the `!` prefix works:** When I show you a command starting with `!`, paste the full line (including the `!`) into the Claude Code prompt and press Enter. The `!` tells Claude Code to run it in your terminal — I cannot see the output.

---

## Phase 5 — API Key

Agents need an LLM API key to run. Tell the user:

> Agents need an LLM provider to run. I will open your config file — you just need to paste your key into it.

First, ensure the `.env` has restricted permissions before opening it for editing:

```bash
chmod 600 "$HOME/.syntropic137/.env"
```

Then tell the user:
>
> **Step 1:** Get your key ready:
> - **Anthropic API key:** https://console.anthropic.com/settings/keys — copy it to your clipboard
> - **Or** if you use Claude Code with an OAuth token, copy that instead
>
> **Step 2:** Paste one of these commands into the Claude Code prompt and press Enter:

**On macOS:**
> ```
> ! open -t ~/.syntropic137/.env
> ```

**On Linux:**
> ```
> ! ${EDITOR:-nano} ~/.syntropic137/.env
> ```

> **Step 3:** In the editor, find the line that says:
> - `ANTHROPIC_API_KEY=` — paste your Anthropic key right after the `=`
> - **Or** scroll to `CLAUDE_CODE_OAUTH_TOKEN=` and paste your OAuth token there instead
> - (Only one is needed — the file has comments explaining both)
>
> **Step 4:** Save and close the file.

On Linux with nano, add: *(nano: `Ctrl+O` then `Enter` to save, `Ctrl+X` to exit)*

> Let me know when done.

After the user confirms, enforce permissions and verify the key was written (without revealing it):

```bash
chmod 600 "$HOME/.syntropic137/.env"
grep -q '^ANTHROPIC_API_KEY=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "apikey:set" || \
  grep -q '^CLAUDE_CODE_OAUTH_TOKEN=.' "$HOME/.syntropic137/.env" 2>/dev/null && echo "oauth:set" || \
  echo "key:missing"
```

**Never ask the user to paste a key or token into the chat. Never echo or log the value.**

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

## Phase 7 — Cloudflare Tunnel (if selected)

**Only run this phase if the user selected optional feature [1].**

> **Why Cloudflare comes before GitHub App:** The GitHub App webhook URL must point to your public hostname. Set up the tunnel first so you have the URL ready to enter when creating the GitHub App.

Tell the user:

> Setting up a Cloudflare tunnel to give your instance a public URL. We do this before the GitHub App so you have the webhook URL ready.
>
> 1. Open the Cloudflare Zero Trust dashboard:
>    https://dash.cloudflare.com/?to=/:account/networks-tunnels
>
> 2. Click **"Create a tunnel"** and choose **"Cloudflared"**
>
> 3. Name it something like `syntropic137`
>
> 4. On the **"Install and run connectors"** step, Cloudflare shows an install command like:
>    ```
>    cloudflared service install eyJhIjoi...
>    ```
>    Copy the **full command** — you do NOT need to extract the token yourself.
>
> 5. **Don't wait for the connector to connect.** The wizard won't let you proceed to routes from here. Instead, go back to **Networks > Tunnels** in the sidebar.
>
> 6. Click on your tunnel name in the list, then go to the **"Public Hostname"** tab.
>
> 7. Click **"Add a public hostname"** and configure:
>    - **Subdomain:** your chosen subdomain (e.g., `syn`)
>    - **Domain:** select your domain
>    - **Service type:** `HTTP`
>    - **URL:** `localhost:8137`
>
> 8. Save.
>
> You now have two things: the install command (with token) and your public hostname. Tell me when ready.

Now have the user save the tunnel token and hostname. First ensure permissions, then open the `.env` file:

```bash
chmod 600 "$HOME/.syntropic137/.env"
```

> Now save the tunnel token and your public hostname.
>
> Paste one of these commands into the Claude Code prompt to open your config:

**On macOS:**
> ```
> ! open -t ~/.syntropic137/.env
> ```

**On Linux:**
> ```
> ! ${EDITOR:-nano} ~/.syntropic137/.env
> ```

> Find the **CLOUDFLARE TUNNEL** section and fill in:
> - `CLOUDFLARE_TUNNEL_TOKEN=` — paste the **full command** Cloudflare gave you (e.g., `cloudflared service install eyJ...`). It is OK to paste the whole thing — I will extract the token automatically after you save.
> - `SYN_PUBLIC_HOSTNAME=` — type the hostname you configured (e.g., `syn.yourdomain.com`)
>
> Save and close the file.

After the user confirms, enforce permissions, auto-extract the token if they pasted the full command, verify both values, and read back the hostname for confirmation:

```bash
chmod 600 "$HOME/.syntropic137/.env"

# Auto-extract eyJ... token if user pasted full cloudflared command.
# Uses Python so the token never appears in process args (sed would leak via ps).
python3 -c "
import re, os

env_file = os.path.expanduser('~/.syntropic137/.env')
lines = []
tunnel_status = 'tunnel:missing'

with open(env_file) as f:
    for line in f:
        if line.startswith('CLOUDFLARE_TUNNEL_TOKEN='):
            raw = line.strip().split('=', 1)[1]
            m = re.search(r'eyJ[A-Za-z0-9_.=-]+', raw)
            token = m.group(0) if m else raw
            lines.append('CLOUDFLARE_TUNNEL_TOKEN=' + token + '\n')
            if not token:
                tunnel_status = 'tunnel:missing'
            elif token != raw:
                tunnel_status = 'tunnel:extracted (cleaned up full command → token only)'
            else:
                tunnel_status = 'tunnel:set'
        else:
            lines.append(line)

import tempfile
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(env_file))
with os.fdopen(fd, 'w') as f:
    f.writelines(lines)
os.chmod(tmp, 0o600)
os.replace(tmp, env_file)
print(tunnel_status)
"

_syn_hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
echo "hostname:${_syn_hostname}"
```

If the hostname was detected, echo it back for confirmation:

> I detected your public hostname as `<hostname>` — is that correct?

This catches typos before the value is used as the GitHub App webhook URL in Phase 8.

---

## Phase 8 — GitHub App

**Always run this phase — GitHub App is required for agents to interact with GitHub.**

Read the public hostname if Cloudflare was configured (empty string if not):

```bash
_syn_webhook_host=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
```

If `_syn_webhook_host` is set, the webhook URL will be `https://${_syn_webhook_host}/api/v1/github/webhook`. If not set, webhooks will only work locally.

Tell the user:

> Setting up your GitHub App. This creates a private bot that connects to your repos.
>
> I will open the GitHub App creation page in your browser. You will need to fill in a few fields:
>
> - **GitHub App name:** choose any unique name (e.g., `syntropic137-yourname`)
> - **Homepage URL:** `http://localhost:8137` (or your public URL if you have one)
> - **Webhook URL:** `https://<your-public-hostname>/api/v1/github/webhook`
>   *(shown above if Cloudflare was configured)*
> - **Webhook secret:** I will generate one for you — see below

Generate the webhook secret, copy it to the user's clipboard, and save it to `.env` — all without displaying the value:

```bash
! _wh_secret=$(openssl rand -hex 20) && \
  if command -v pbcopy >/dev/null 2>&1; then \
    printf '%s' "$_wh_secret" | pbcopy && _clip="clipboard"; \
  elif command -v xclip >/dev/null 2>&1; then \
    printf '%s' "$_wh_secret" | xclip -selection clipboard && _clip="clipboard"; \
  else \
    _clip=""; \
  fi && \
  printf '%s' "$_wh_secret" | python3 -c "
import sys, os, tempfile
key = 'SYN_GITHUB_WEBHOOK_SECRET'
val = sys.stdin.readline().strip()
env_file = os.path.expanduser('~/.syntropic137/.env')
lines, found = [], False
with open(env_file) as f:
    for line in f:
        if line.startswith(key + '='):
            lines.append(key + '=' + val + '\n')
            found = True
        else:
            lines.append(line)
if not found:
    lines.append(key + '=' + val + '\n')
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(env_file))
with os.fdopen(fd, 'w') as f:
    f.writelines(lines)
os.chmod(tmp, 0o600)
os.replace(tmp, env_file)
" && \
  if [ -n "$_clip" ]; then \
    echo "Webhook secret generated, copied to clipboard, and saved to .env."; \
  else \
    echo "Webhook secret generated and saved to .env."; \
    echo "Clipboard not available — retrieve it with: grep SYN_GITHUB_WEBHOOK_SECRET ~/.syntropic137/.env | cut -d= -f2-"; \
  fi && \
  unset _wh_secret _clip
```

Tell the user:

> **If clipboard was available:** Your webhook secret is in your clipboard (Cmd+V / Ctrl+V). Paste it into the GitHub App creation form under "Webhook secret". It is already saved to `.env` — you do not need to keep it anywhere else.
>
> **If clipboard was not available:** The secret is saved to `.env`. Run the `grep` command shown above to retrieve it for pasting into GitHub.

Open the GitHub App creation page:

```bash
open "https://github.com/settings/apps/new" 2>/dev/null || \
  echo "Please open this URL in your browser: https://github.com/settings/apps/new"
```

After the user creates the app, ask for the App ID and name first:

> After creating the app, GitHub shows you the app settings page. I need:
>
> 1. **App ID** (shown at the top of the General settings page)
> 2. **App name** (the name you entered)

Write App ID and name to `.env`:

```bash
sed -i.bak "s|^SYN_GITHUB_APP_ID=.*|SYN_GITHUB_APP_ID=${APP_ID}|" "$HOME/.syntropic137/.env"
sed -i.bak "s|^SYN_GITHUB_APP_NAME=.*|SYN_GITHUB_APP_NAME=${APP_NAME}|" "$HOME/.syntropic137/.env"
rm -f "$HOME/.syntropic137/.env.bak"
```

If any `.env` key does not already exist as a placeholder, append it instead of using sed.

### Private key handling

Now handle the private key. First, check `~/Downloads` for the most recently downloaded `.pem` file:

```bash
find "$HOME/Downloads" -maxdepth 1 -name '*.pem' -type f -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1
```

If a `.pem` is found, tell the user:

> **Private key:** Click "Generate a private key" on the app settings page. GitHub downloads a `.pem` file to your Downloads folder.
>
> I found this `.pem` in your Downloads:
> `<filename>`
>
> Is this the one? (Or tell me the full path if it downloaded elsewhere.)
>
> **Note:** I will NOT read or open this file — I only need the path so I can move it to a secure location. The contents never enter this conversation. *(If you chose 1Password backup, a local script reads it to store in your vault — still outside this chat.)*

If no `.pem` is found, tell the user:

> **Private key:** Click "Generate a private key" on the app settings page. It downloads a `.pem` file (usually to `~/Downloads/`). Tell me the file path when it is downloaded.
>
> **Note:** I will NOT read or open this file — I only need the path so I can move it to a secure location.

**Security note:** I will only use the file path to move the key to a secure location. I will **never** open or read the `.pem` file — the contents stay on your filesystem. The original is deleted from Downloads after the move. *(Exception: if you chose 1Password backup in Phase 9, the PEM contents are read by a local Python script and sent to `op item create` via stdin — never through Claude's context window.)*

Once the user confirms the path, move the `.pem` to the secrets directory and set permissions. Back up any existing key first. **NEVER use Read, cat, or any tool to view the `.pem` contents — only move the file:**

```bash
_dest="$HOME/.syntropic137/secrets/github-app-private-key.pem" && \
  if [ -e "$_dest" ]; then \
    _bak="${_dest}.$(date +'%Y%m%d-%H%M%S').bak" && \
    mv "$_dest" "$_bak" && \
    echo "Existing key backed up to: $_bak"; \
  fi && \
  mv "<user-provided-path>" "$_dest" && \
  chmod 600 "$_dest" && \
  unset _dest _bak && \
  echo "Private key moved to secrets/ (original removed)."
```

Verify the key file exists (size check only, never read contents):

```bash
test -s "$HOME/.syntropic137/secrets/github-app-private-key.pem" && echo "pem:ok" || echo "pem:missing"
```

That is all that is needed for the private key. The compose file automatically mounts `secrets/github-app-private-key.pem` as a Docker secret (tmpfs — never written to disk) and sets `SYN_GITHUB_APP_PRIVATE_KEY_FILE=/run/secrets/github_app_private_key` on the containers. No `.env` entry is required for the key path.

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

> All secrets backed up to 1Password vault "syntropic137", item "syntropic137-config". You can restore on a new machine with `./syn-ctl secrets-pull`.

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
_hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
```

Present the post-setup summary to the user. If a public hostname is configured, show both local and public URLs:

```
Syntropic137 is running!
═══════════════════════════════════════════════════

 Dashboard:   http://localhost:8137 (local)
 Dashboard:   https://<hostname> (public — via Cloudflare tunnel)
 Pulse UI:    http://localhost:8137/pulse/ (local)
 Pulse UI:    https://<hostname>/pulse/ (public)
 API Docs:    http://localhost:8137/docs (local)
 API Docs:    https://<hostname>/docs (public)
 Version:     <version from health endpoint>

 WHAT'S NEXT:

 1. Open the dashboard -- see your platform overview
 2. Open Pulse -- view the contribution heatmap and activity
 3. Create your first workflow:
    "Create a workflow that reviews PRs on my repo"
 4. Trigger a manual run:
    /syn-workflow run <workflow-id> --task "Hello world"
 5. Set up automatic PR triggers:
    "Set up triggers for my-org/my-repo"

 Run /syn-setup again anytime to add features or update.
═══════════════════════════════════════════════════
```

If no public hostname is configured, show only the local URLs (without the "(local)" suffix):

```
Syntropic137 is running!
═══════════════════════════════════════════════════

 Dashboard:   http://localhost:8137
 Pulse UI:    http://localhost:8137/pulse/
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
