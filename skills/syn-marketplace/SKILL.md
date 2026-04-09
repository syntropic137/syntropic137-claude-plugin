---
name: syn-marketplace
description: Browse, install, update, export, and publish Syntropic137 workflows via GitHub repositories — the self-hosted workflow marketplace
argument-hint: <list|add|install|installed|update|remove|export|publish> [args]
model: sonnet
---

# /syn-marketplace — Workflow Marketplace

The Syntropic137 marketplace is distributed — workflows are shared as files in GitHub repos. You register a GitHub repo as a "source", then install individual workflows from it. There is no central registry yet (planned). All operations use the `syn` CLI or the platform API directly.

If `syn` is not installed, run `npx @syntropic137/setup cli` first.

## Consuming Workflows

### Browse available sources

```bash
curl http://localhost:8137/api/v1/marketplace/sources
```

If no sources are registered yet, add one first.

### Add a GitHub repo as a source

```bash
syn marketplace add https://github.com/syntropic137/workflow-library
```

Or via API:
```bash
curl -X POST http://localhost:8137/api/v1/marketplace/sources \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/syntropic137/workflow-library"}'
```

### List available workflows

```bash
syn marketplace list
```

### Install a workflow from a trusted source

```bash
syn marketplace install <workflow-name>
```

### See what's installed

```bash
syn marketplace installed
```

Or via API: `curl http://localhost:8137/api/v1/marketplace/installed`

### Update an installed workflow

```bash
syn marketplace update <workflow-name>   # update one
syn marketplace update                   # update all
```

### Remove a source

```bash
syn marketplace remove <source-url-or-id>
```

## Publishing Workflows

### Export a workflow for sharing

```bash
syn marketplace export <workflow-id>
syn marketplace export <workflow-id> --output ./my-workflow.yaml
```

Or via API: `curl http://localhost:8137/api/v1/workflows/<id>/export`

This downloads the workflow YAML. The output file defaults to `./workflow-export.json` if `--output` is not specified.

### Publish to a GitHub repo

There is no automated publish command yet. The manual steps are:

1. Export the workflow: `syn marketplace export <workflow-id> --output ./workflow.yaml`
2. Copy the YAML into the `workflows/` directory of your GitHub repo
3. Push the repo
4. Others install it with: `syn marketplace add https://github.com/owner/repo`

## API URL Resolution

All API calls default to `http://localhost:8137`. If a custom hostname is configured, read it from `SYN_PUBLIC_HOSTNAME` in `~/.syntropic137/.env`, or set `SYN_API_URL` in the environment.

## Errors

On API errors, run `/syn-health` to diagnose platform status.
