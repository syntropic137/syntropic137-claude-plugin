---
name: marketplace
description: Search, install, and manage Syntropic137 workflow plugins from marketplace registries — browse available workflows, review before installing, manage registry sources
---

# Marketplace — Syntropic137

Use this knowledge when the user wants to browse, install, or manage workflow plugins from marketplace registries, or set up a new marketplace source.

## What is a Marketplace?

A marketplace is a GitHub repository containing validated Syntropic137 workflow plugins. Each plugin packages one or more workflows with optional trigger examples. The `syn` CLI can register marketplace repos, search their indexes, and install plugins.

The default Syntropic137 marketplace is `syntropic137/syntropic137-marketplace`.

## Registry Management

Marketplaces are registered locally and their indexes are cached (4-hour TTL).

```bash
# Register the default marketplace
syn marketplace add syntropic137/syntropic137-marketplace

# Register a third-party marketplace
syn marketplace add yourorg/your-marketplace

# List registered marketplaces
syn marketplace list

# Remove a marketplace
syn marketplace remove <name>

# Force refresh cached indexes
syn marketplace refresh
```

## Browsing Workflows

```bash
# Search across all registered marketplaces
syn workflow search "code review"
syn workflow search "deployment"
syn workflow search ""               # Browse all available

# Get details about a specific plugin before installing
syn workflow info code-review
syn workflow info sdlc-trunk
```

## Installing Plugins

Plugins can be installed by name (from a registered marketplace) or directly from a Git URL:

```bash
# Install from registered marketplace (by name)
syn workflow install code-review
syn workflow install sdlc-trunk

# Install directly from a GitHub repo
syn workflow install github.com/yourorg/your-plugin

# Install from a local directory (for development)
syn workflow install ./path/to/plugin

# List installed plugins
syn workflow installed

# Update an installed plugin
syn workflow update code-review

# Remove a plugin
syn workflow uninstall code-review
```

### What Happens During Install

1. CLI resolves the source (marketplace index, Git clone, or local path)
2. Reads `syntropic137-plugin.json` manifest
3. Parses and validates each `workflow.yaml` against the platform schema
4. Resolves all phase prompt files (`phases/*.md`) inline
5. POSTs each workflow to the API
6. Records the installation locally

### After Installing

- Verify with `syn workflow list` — installed workflows appear
- Trigger definitions in plugins are **examples only** — they show which GitHub events and conditions are relevant, but users set up triggers manually with `syn triggers register`
- Run a workflow: `syn workflow run <workflow-id> --input key=value`

## Validation

The CLI validates workflow definitions against the platform's schema during install. You can also validate manually:

```bash
syn workflow validate ./path/to/workflow.yaml
```

## Security Considerations

Before installing plugins from third-party marketplaces:

- **Review the source** — plugins contain phase prompts that instruct agents. Check for suspicious patterns in `phases/*.md` files
- **Check tool access** — review `allowed_tools` declarations in workflow definitions. Be cautious of plugins requesting broad tool access (especially `edit` and `bash`) without clear justification
- **Use the security-reviewer agent** — ask Claude to review a marketplace or plugin for security before installing

Plugins execute with the same permissions as any workflow on your platform. Treat third-party plugins like any other code dependency — review before installing.

## The Default Marketplace

The official Syntropic137 marketplace (`syntropic137/syntropic137-marketplace`) includes:

| Plugin | Workflows | Description |
|--------|-----------|-------------|
| `code-review` | 1 | AI-powered PR code review |
| `sdlc-trunk` | 3 | Full trunk-based dev lifecycle — PR review, CI self-healing, release prep |

### Quick Start

```bash
# Register and install everything
syn marketplace add syntropic137/syntropic137-marketplace
syn workflow install code-review
syn workflow install sdlc-trunk
syn workflow list    # Verify: 4 workflows created
```

## Common Scenarios

### "Set up the default marketplace workflows"

1. Register the marketplace: `syn marketplace add syntropic137/syntropic137-marketplace`
2. Install plugins: `syn workflow install code-review && syn workflow install sdlc-trunk`
3. Verify: `syn workflow list`
4. Set up triggers as needed: see the github-automation skill

### "Find a workflow for PR reviews"

1. Search: `syn workflow search "review"`
2. Inspect: `syn workflow info code-review`
3. Install: `syn workflow install code-review`

### "What plugins do I have installed?"

```bash
syn workflow installed
```

### "Remove a plugin I no longer need"

```bash
syn workflow uninstall code-review
```
