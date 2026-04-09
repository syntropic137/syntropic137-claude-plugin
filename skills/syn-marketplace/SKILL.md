---
name: syn-marketplace
description: Browse, install, update, export, and publish Syntropic137 workflows via GitHub repositories — the self-hosted workflow marketplace
argument-hint: <list|add|install|installed|update|remove|export|publish> [args]
model: sonnet
---

# /syn-marketplace — Workflow Marketplace

Use this skill when you need to find, install, or share workflow plugins. The Syntropic137 marketplace is distributed — workflows live in GitHub repos, not a central registry. You register a repo as a source, then install individual workflows from it.

## When to Use This

Use `/syn-marketplace` when you want to: browse workflows available in registered sources, install a community workflow, update installed plugins to the latest version, export one of your workflows to share, or register a new source repo.

For the **security model** behind plugin installation — what to check before installing third-party workflows, what `allowed_tools` declarations mean — the marketplace skill has the full guide.

## The Distributed Marketplace Model

There is no central registry. Anyone can create a marketplace by making a GitHub repo with workflow YAML files. You register repos you trust, browse their contents, and install specific workflows.

The official Syntropic137 marketplace is `syntropic137/syntropic137-marketplace` — includes `code-review` and `sdlc-trunk` (3 workflows for PR review, CI self-healing, release prep).

**Before installing third-party plugins:** review the phase prompts in `phases/*.md` and check the `allowed_tools` declarations. Plugins execute with full agent permissions.

## Core Commands

```bash
# Sources (registered GitHub repos)
syn marketplace add syntropic137/syntropic137-marketplace
syn marketplace add yourorg/your-marketplace
syn marketplace list
syn marketplace remove <name>
syn marketplace refresh                  # force re-fetch cached indexes

# Browsing
syn workflow search "code review"
syn workflow search ""                   # browse all
syn workflow info code-review            # details before installing

# Installing
syn workflow install code-review
syn workflow install github.com/yourorg/your-plugin   # direct from URL
syn workflow install ./path/to/plugin                  # local path (dev)
syn workflow installed                   # what's installed
syn workflow update code-review          # update to latest
syn workflow uninstall code-review

# Exporting
syn marketplace export <workflow-id>
syn marketplace export <workflow-id> --output ./workflow.yaml
```

## Common Scenarios

**"Set up the official Syntropic137 workflows."**
1. `syn marketplace add syntropic137/syntropic137-marketplace`
2. `syn workflow install code-review`
3. `syn workflow install sdlc-trunk`
4. `syn workflow list` — verify 4 workflows are registered
5. Set up trigger rules: see `/syn-triggers`

**"I built a workflow and want to share it with my team."**
1. `syn marketplace export <workflow-id> --output ./my-workflow.yaml`
2. Add the YAML to a `workflows/` directory in a GitHub repo
3. Push the repo
4. Team members: `syn marketplace add yourorg/your-repo` → `syn workflow install my-workflow`

**"I want to check what's installed before running anything."**
`syn workflow installed` — lists all installed plugin workflows with their source.

## Errors

On API errors, run `/syn-health`. For full security guidance on plugin installation, see the marketplace skill.
