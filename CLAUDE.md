# syntropic137-claude-plugin

Claude Code plugin for the Syntropic137 platform: commands (`/syn-*`) and skills for orchestration, observability, and setup.

## Versioning

**Single source of truth:** `.claude-plugin/plugin.json`, `version` field.

**How releases work:**

1. Make your changes (commands, skills, hooks).
2. Bump the version in `.claude-plugin/plugin.json` in the **same commit or a follow-up commit** on `main`.
3. Push to `main`.
4. CI (`.github/workflows/plugin-tag.yml`) compares `version` in the pushed commit vs the previous commit. If it changed, it creates and pushes the `v<version>` git tag automatically.

**Rules:**
- Always bump `plugin.json` when shipping user-visible changes: CI only tags on a version diff.
- Never manually push a tag that matches a version already in `plugin.json` on `main`: CI will try to create the same tag and fail with "already exists". If you already pushed a tag manually, CI silently skips (idempotent guard), so this is recoverable.
- Use semver: `patch` for fixes/copy changes, `minor` for new commands or skills, `major` for breaking changes.
- Do **not** bump the version in the same commit as the code change if you want a clean one-liner history: a separate `chore: bump plugin version to x.y.z` commit is fine.

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

## Updating the Plugin (User-Side)

The plugin is published as `syntropic137@syntropic137` (plugin name `@` marketplace org).

```bash
# 1. Refresh the marketplace catalog
claude plugin marketplace update syntropic137

# 2. Update the plugin to the latest version
claude plugin update syntropic137@syntropic137
```

First-time install:

```bash
claude plugin marketplace add syntropic137
claude plugin install syntropic137@syntropic137
```

## Hooks

`hooks/hooks.json` is **loaded automatically** by Claude Code: do NOT reference it in `plugin.json`. Only add a `"hooks"` field to `plugin.json` if you have a *second* hooks file at a non-standard path.

## Security

See [./SECURITY.md](./SECURITY.md) for the full security model. The critical rule: **secrets must never enter Claude's context window.** All credential input uses `!` prefix (external shell execution), file paths instead of file content, and `grep -q` status checks instead of value reads. Contributors must follow these patterns: see the rules in SECURITY.md before touching any setup or secrets code.

## Claude Code Documentation

When authoring workflow phases, skills, or commands, reference the official Claude Code docs:

- Commands reference: https://code.claude.com/docs/en/commands.md
- Skills reference: https://code.claude.com/docs/en/skills.md

Each Syntropic137 workflow phase is a Claude CLI invocation. Phase prompts can invoke slash commands and skills directly. Workflow authors should be familiar with what commands and skills are available.

## Writing Style

Use colons `:` and commas `,` instead of dashes or em dashes in prose. This applies to all skill files, commands, and documentation.

## Scratch files

Root-level `.md` files (except `README.md`, `CLAUDE.md`, `SECURITY.md`) are scratch: never commit them.
