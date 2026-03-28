# Security Practices

This plugin handles API keys, tokens, and private keys during setup. Every secret flow is designed so that **sensitive values never enter Claude's context window**.

## Core Principles

1. **Secrets stay in the shell.** All credential input uses the `!` prefix (Claude Code external execution) with `read -rsp` (silent prompt). The value goes straight to a file — Claude never sees it.
2. **Private keys are paths, not content.** The user provides a file path to their `.pem`; the plugin moves it to `~/.syntropic137/secrets/` with `chmod 600` and deletes the original from Downloads. The adapter reads the raw `.pem` directly — no encoding step needed. The key is never read into context.
3. **Generated secrets go to files or clipboard.** `openssl rand` output is redirected to files or piped to `pbcopy` — never echoed to the conversation.
4. **Verification is status-only.** Checks use `grep -q` and return "set/missing" — never the actual value.
5. **1Password uses stdin piping.** Backup reads secrets from disk in a Python script and pipes JSON to `op item create --template=-`. No secret is passed as a CLI argument (visible in `ps aux`) or displayed in output.
6. **File permissions are restrictive.** All secret files get `chmod 600` (owner read/write only).

## Secret Flow Patterns

| Phase | Secret | Method | Context-safe? |
|-------|--------|--------|---------------|
| 5 — API Key | `ANTHROPIC_API_KEY` | `! read -rsp` → `sed` to `.env` | Yes |
| 6 — Infra secrets | DB, Redis, MinIO passwords | `openssl rand -hex 32 >` file | Yes |
| 7 — Cloudflare | `CLOUDFLARE_TUNNEL_TOKEN` | `! read -rsp` → auto-extract `eyJ...` token → `sed` to `.env` | Yes |
| 8 — GitHub App | Webhook secret | `! openssl rand -hex 20 | pbcopy` → clipboard only | Yes |
| 8 — GitHub App | Private key `.pem` | `mv` to secrets dir, `chmod 600`, original deleted from Downloads | Yes |
| 9 — 1Password | All secrets | Python reads disk → stdin pipe to `op` | Yes |

## Rules for Contributors

- **Never** ask the user to paste a key or token into the chat.
- **Never** use `Read` or `cat` on a file containing secrets (`.env`, `*.secret`, `*.pem`).
- **Never** pass secret values as CLI arguments — use stdin piping or file redirection.
- **Never** echo or log secret values — confirmation messages only ("Key saved", "Token saved").
- **Always** use `chmod 600` on files containing secrets.
- **Always** use the `!` prefix for commands that accept secret input.
- **Always** mark 1Password fields as `type: CONCEALED`.

## Clipboard Pattern (macOS)

When a generated secret must be shared with the user (e.g., webhook secret for pasting into GitHub's UI), use clipboard instead of display:

```bash
! openssl rand -hex 20 | tee >(pbcopy) > "$HOME/.syntropic137/.webhook-secret-tmp" && echo "Webhook secret generated and copied to clipboard."
```

The secret reaches the clipboard and a temp file (for `.env` write) but never appears in Claude's output.

## Cloudflare Token Parsing

Cloudflare presents tunnel tokens inside an install command (`cloudflared service install eyJ...`). The setup flow accepts either the full command or a bare token and auto-extracts the `eyJ`-prefixed token (base64 JSON). This matches the pattern in `syntropic137/infra/scripts/cloudflare_tunnel.py:extract_token()`.

## Private Key Handling

The setup flow for GitHub App private keys:

1. Auto-detects the most recent `.pem` in `~/Downloads/` (or user provides path)
2. Moves the `.pem` to `~/.syntropic137/secrets/github-app-private-key.pem` with `chmod 600`
3. Deletes the original from Downloads — only the secrets directory copy remains
4. `.env` stores the container-internal path (`/run/secrets/github-app-private-key.pem`)

The adapter reads the raw `.pem` directly via `decode_private_key()` in `client_jwt.py` (supports both raw PEM and legacy base64-encoded keys per syntropic137/syntropic137#363).

## Threat Model

| Threat | Mitigation |
|--------|------------|
| Secret in Claude's context window | `!` prefix, file-only I/O, `grep -q` verification |
| Secret in process list (`ps aux`) | stdin piping, never CLI args |
| Secret on disk with wrong perms | `chmod 600` on all secret files |
| Secret lost after setup | 1Password backup (Phase 9) |
| Unprotected API after setup | Security smoke test (Phase 11) |
