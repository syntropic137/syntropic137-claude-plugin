---
name: syn-workflow
description: Manage Syntropic137 workflows; packages (installed packages), list (platform-registered), show, run, create, install, update, validate, delete, and check execution status
argument-hint: <packages|list|show|run|create|install|update|validate|delete|status> [args]
model: sonnet
---

# /syn-workflow: Workflow Management

Use this skill when you need to interact with workflow templates and executions from the command line. All operations use the `syn` CLI. Install it with `npx @syntropic137/setup cli` if not present.

## When to Use This

Use `/syn-workflow` when you want to: browse what workflows exist (`list`, `packages`), inspect a workflow's phases and inputs (`show`), kick off a run (`run`), validate a YAML definition before registering it (`validate`), or register and update one (`create --from`, `install`, `update`).

For **designing** a new workflow template from scratch, the workflow-management skill has the full conceptual model and the YAML schema, including which keys are rejected. For **monitoring a running execution**, use `/syn-control`.

## packages vs list: Two Different Things

**`packages`**: the workflow packages this CLI has installed with `syn workflow install` (local install history in `~/.syntropic137/workflows/installed.json`): package name, version, source, workflow count, install time.

```
syn workflow packages
```

**`list`**: workflows currently registered in the running Syntropic137 instance. These are what the platform can actually execute:

```
syn workflow list
```

To see a workflow's inputs before running it, use `syn workflow show <id>`: it prints each declared input with whether it is required and its default.

## Core Commands

```bash
syn workflow packages                          # packages installed by this CLI
syn workflow list                              # platform-registered workflows
syn workflow list --include-archived           # include archived templates
syn workflow show <id>                         # phases, config, declared inputs
syn workflow run <id> --task "Fix auth bug" -R owner/repo
syn workflow run <id> -t "Review PR 42" -R owner/repo -i base_branch=develop
syn workflow validate path/to/workflow.yaml    # a file or a package directory
syn workflow create "My workflow" --from path/to/workflow.yaml   # register or update one file
syn workflow install path/to/package/          # register or update a package (also git URL, org/repo, marketplace name)
syn workflow install path/to/package/ --force  # overwrite the same version on purpose
syn workflow update <package-name>             # re-resolve an installed package from its source
syn workflow delete <id> --force               # archive a workflow
syn workflow status <execution-id>             # check a running execution
```

Short alias: `syn run <id> -t "task description"`

Flags: `-t/--task` supplies `$ARGUMENTS` (the `task` input), `-i name=value` supplies any other declared input, and `-R owner/repo` (repeatable) supplies the repositories. Repositories are never passed as an input: `repository` and `repos` are reserved input names.

## Common Scenarios

**"I want to run a workflow but don't know its inputs."**
1. `syn workflow show <id>` to see required and optional inputs
2. `syn workflow run <id> -t "..." -R owner/repo -i key=value` for each required input

**"I want to check if a workflow is already registered."**
`syn workflow list`; if it's not there, install it from the marketplace or validate + register your YAML.

**"I wrote a new workflow YAML and want to use it."**
1. `syn workflow validate ./my-workflow.yaml` to catch errors before registering
2. `syn workflow create "My workflow" --from ./my-workflow.yaml`, or `syn workflow install ./my-package/` for a package directory (needed when phases use `prompt_file`)

**"I changed a workflow and want to update it in place."**
Re-register it the same way you first did. The YAML `id` is the platform id, so the same `id` updates the existing workflow.
- First registered with `create --from`: re-run the same `create --from` command.
- First registered with `install`: bump `version` in the package's `syntropic137-plugin.json` and re-run `syn workflow install <dir>`, or re-run it with `--force` to overwrite the same version (`0.0.0` when there is no manifest). For git or marketplace sources, `syn workflow update <package-name>`.

If you see `installed with version 0.0.0, but this install declares no version. Refusing to overwrite recorded provenance`, the workflow was installed with `syn workflow install` and you tried to update it with `create --from`. Do not add `version:` to the YAML (it is rejected); use `syn workflow install <dir> --force` instead. See the workflow-management skill, "Updating a Workflow In Place".

## Errors

On errors, run `/syn-health` to check platform status. For validator rejections and deep workflow design questions, see the workflow-management skill. Run `syn workflow --help` for full flag reference.
