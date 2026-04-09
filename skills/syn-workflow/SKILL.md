---
name: syn-workflow
description: Manage Syntropic137 workflows — packages (local cache), list (platform-registered), show, run, create, validate, delete, and check execution status
argument-hint: <packages|list|show|run|create|validate|delete|status> [args]
model: sonnet
---

# /syn-workflow — Workflow Management

Use this skill to manage Syntropic137 workflow templates and executions from inside Claude Code. All operations go through the `syn` CLI. If `syn` is not installed, run `npx @syntropic137/setup cli` first.

## packages vs list

These are two distinct things:

- **`packages`** — locally cached workflow YAML definitions on disk (`~/.syntropic137/workflows/` or `./workflows/` in dev). These are downloaded but may not yet be registered in the running platform.
- **`list`** — workflows currently registered in the running Syntropic137 instance (what the platform knows about and can execute).

## Workflow Packages

List locally cached workflow packages and their required inputs:

```bash
syn workflow packages
```

Output shows each package name with its `input_declarations` — the Required and Optional inputs you'll need to supply when running it:

```
Local workflow packages (~/.syntropic137/workflows/):

  github-pr-review
    Required: pr_url, repository
    Optional: branch  [default: main]

  self-healing-ci
    Required: workflow_id, repository
```

This was renamed from `installed` in earlier versions of the CLI.

If `syn` is not available, inspect a package's inputs directly:
```bash
python3 -c "import yaml, sys; d=yaml.safe_load(open(sys.argv[1])); [print(i) for i in d.get('input_declarations',[])]" ~/.syntropic137/workflows/my-workflow.yaml
```

## List Platform-Registered Workflows

```bash
syn workflow list
syn workflow list --include-archived   # include archived templates
```

## Show, Run, Create, Validate

```bash
syn workflow show <id>
syn workflow run <id> --task "refactor auth module"
syn workflow run <id> --task "fix bug" --input repository=owner/repo
syn workflow create --type implementation --repo owner/repo --description "Feature X"
syn workflow validate path/to/workflow.yaml
syn workflow delete <id>
syn workflow delete <id> --force
syn workflow status <execution-id>
```

Run `syn workflow --help` for full flag reference, or check `docs.syntropic137.com/docs/cli` for the complete CLI docs.

On errors, run `/syn-health` to check platform status.
