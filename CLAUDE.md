# syntropic137-claude-plugin

Claude Code plugin for the Syntropic137 platform — commands (`/syn-*`) and skills for orchestration, observability, and setup.

## Versioning

**Single source of truth:** `.claude-plugin/plugin.json` → `version` field.

**How releases work:**

1. Make your changes (commands, skills, hooks).
2. Bump the version in `.claude-plugin/plugin.json` in the **same commit or a follow-up commit** on `main`.
3. Push to `main`.
4. CI (`.github/workflows/plugin-tag.yml`) compares `version` in the pushed commit vs the previous commit. If it changed, it creates and pushes the `v<version>` git tag automatically.

**Rules:**
- Always bump `plugin.json` when shipping user-visible changes — CI only tags on a version diff.
- Never manually push a tag that matches a version already in `plugin.json` on `main` — CI will try to create the same tag and fail with "already exists". If you already pushed a tag manually, CI silently skips (idempotent guard), so this is recoverable.
- Use semver: `patch` for fixes/copy changes, `minor` for new commands or skills, `major` for breaking changes.
- Do **not** bump the version in the same commit as the code change if you want a clean one-liner history — a separate `chore: bump plugin version to x.y.z` commit is fine.

**Example flow:**

```
# Fix a command
git add commands/syn-setup.md
git commit -m "fix(syn-setup): ..."

# Bump version
# edit .claude-plugin/plugin.json: "version": "0.5.2"
git add .claude-plugin/plugin.json
git commit -m "chore: bump plugin version to 0.5.2"

git push origin main
# → CI tags v0.5.2 automatically
```

## Scratch files

Root-level `.md` files (except `README.md`, `CLAUDE.md`) are scratch — never commit them.
