---
name: syn-workflow
description: Manage Syntropic137 workflows — packages (local cache), list (platform-registered), show, run, create, validate, delete, and check execution status
argument-hint: <packages|list|show|run|create|validate|delete|status> [args]
model: sonnet
---

# /syn-workflow — Workflow Management

Use this skill when you need to interact with workflow templates and executions from the command line. All operations use the `syn` CLI. Install it with `npx @syntropic137/setup cli` if not present.

## When to Use This

Use `/syn-workflow` when you want to: browse what workflows exist (`list`, `packages`), inspect a workflow's phases (`show`), kick off a run (`run`), or validate a YAML definition before registering it (`validate`).

For **designing** a new workflow template from scratch, the workflow-management skill has the full conceptual model and YAML schema. For **monitoring a running execution**, use `/syn-control`.

## packages vs list — Two Different Things

**`packages`** — locally cached workflow YAMLs on disk (`~/.syntropic137/workflows/` or `./workflows/`). These are downloaded definitions that may not yet be registered in the running platform. Shows the `input_declarations` (Required/Optional inputs) for each:

```
syn workflow packages
```

```
Local workflow packages (~/.syntropic137/workflows/):

  github-pr-review
    Required: pr_url, repository
    Optional: branch  [default: main]

  self-healing-ci
    Required: workflow_id, repository
```

**`list`** — workflows currently registered in the running Syntropic137 instance. These are what the platform can actually execute:

```
syn workflow list
```

**The common pattern:** browse `packages` to see what inputs a workflow needs before running it, then use `list` to confirm it's registered, then `run` it.

## Core Commands

```bash
syn workflow packages                          # locally cached workflow definitions
syn workflow list                              # platform-registered workflows
syn workflow list --include-archived           # include archived templates
syn workflow show <id>                         # phase definitions, config, input declarations
syn workflow run <id> --task "Fix auth bug"
syn workflow run <id> --task "Review PR" --input repository=owner/repo
syn workflow validate path/to/workflow.yaml    # validate before registering
syn workflow delete <id>
syn workflow delete <id> --force               # skip confirmation
syn workflow status <execution-id>             # check a running execution
```

Short alias: `syn run <id> -t "task description"`

## Common Scenarios

**"I want to run a workflow but don't know its inputs."**
1. `syn workflow packages` — shows required and optional inputs per workflow
2. `syn workflow run <id> --task "..." --input key=value` for each required input

**"I want to check if a workflow is already registered."**
`syn workflow list` — if it's not there, install it from the marketplace or validate + register your YAML.

**"I wrote a new workflow YAML and want to use it."**
1. `syn workflow validate ./my-workflow.yaml` — catch errors before registering
2. `syn workflow create --type implementation --repo owner/repo --description "..."` — or `just seed-workflows` in the source repo

## Errors

On errors, run `/syn-health` to check platform status. For deep workflow design questions, see the workflow-management skill. Run `syn workflow --help` for full flag reference.
