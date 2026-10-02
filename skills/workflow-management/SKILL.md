---
name: workflow-management
description: Create, configure, and manage Syntropic137 workflow templates (phase definitions, agent config, YAML schema, $ARGUMENTS substitution, inputs, updating an installed workflow, and design patterns like RIPER-5)
---

# Workflow Management: Syntropic137

When you need to build a new automated workflow, or understand why an existing one behaves unexpectedly, start here. Workflows are the core unit of work: YAML-defined multi-phase agent pipelines that run in isolated Docker workspaces.

**NEVER hardcode task descriptions or repository names into phase prompts.** Use `$ARGUMENTS` for the task and `{{repo_url}}` for the repository (supplied at run time with `-R owner/repo`) so the same template works for any repo and any task.

## When to Use This Skill

Use this when you are: designing a new workflow template, debugging unexpected phase behavior, choosing the right design pattern (RIPER-5 vs lighter options), or understanding the input/output wiring between phases.

Not needed when you just want to **run** an existing workflow; use the execution-control skill instead. Not needed when you want to list or inspect already-registered workflows; use `/syn-workflow` for that.

## Phases Are Headless Agent Sessions

Each workflow phase is one headless agent invocation. Which harness runs it is chosen **per phase** in the workflow YAML `agent` block: `provider: claude` runs `claude -p`, `provider: codex` runs `codex exec`. Claude is the default when no `agent` block is present.

On a **claude** phase, the prompt can invoke any slash command (`/syn-*`, `/commit`, `/review`, etc.) and any installed skill directly by name. When designing one, consult the Claude Code commands and skills references to know what's available:

- Commands: https://code.claude.com/docs/en/commands.md
- Skills: https://code.claude.com/docs/en/skills.md

Write a claude phase prompt the same way you'd write instructions to Claude Code in a terminal session.

On a **codex** phase, write the prompt as plain instructions. Slash commands, Claude plugins, hook events, subagent tracking, and TodoWrite are Claude-only, so a codex phase gets none of them. Anything a phase prompt needs from that list is a reason to keep the phase on claude.

## The Core Model: Templates vs Executions

A **workflow template** is a reusable definition (like a class). A **workflow execution** is a running instance (like an object). One template can have many concurrent executions with different tasks, repos, and inputs.

Templates define **phases**: each phase is one headless agent invocation in its own workspace, on whichever harness that phase declares. Phases always run sequentially, in `order`, and outputs from earlier phases feed later ones via `{{<phase-id>}}` substitution.

**Phase workspaces are ephemeral.** Each phase starts in a fresh Docker container: no git branches, staged files, commits, or file changes from a prior phase carry over. The only thing that crosses a phase boundary is the artifact output. If a phase needs to do git work (commit, push, `gh pr create`), it must do so in the same phase that made the changes. If a later phase needs those changes, either collapse the phases or have the earlier phase output a patch/diff artifact that the later phase applies.

## YAML Schema Reference

The platform validates workflow YAML against a strict schema: **every unknown key is rejected**, at the workflow, phase, `agent`, and input level. There is no "ignored but harmless" key. Run `syn workflow validate` before registering and fix what it names.

### A complete, valid workflow

```yaml
id: research-then-implement        # stable id; `syn workflow run <id>` resolves it
name: Research then implement
description: Investigate a task, then implement it and open a PR
type: implementation               # research | planning | implementation | review | deployment | custom
classification: standard           # simple | standard | complex | epic

inputs:                            # the ONLY key for declaring inputs
  - name: task
    description: What to implement or fix
    required: true
  - name: base_branch
    description: Branch the PR targets
    required: false
    default: main

phases:
  - id: research                   # the key is `id`, not `phase_id`
    name: Research
    order: 1                       # required, unique; phases run in this order
    description: Map the relevant code before changing anything
    output_artifacts: [research_notes]
    delivers_repo_changes: false   # this phase delivers a report, not a branch
    timeout_seconds: 900
    agent:
      provider: claude
      model: sonnet
    prompt_template: |
      Investigate how to do the following in {{repo_url}}: $ARGUMENTS
      Write your findings as a concise report.

  - id: implement
    name: Implement
    order: 2
    input_artifacts: [research_notes]
    output_artifacts: [pull_request]
    agent:
      provider: claude
      model: opus
      allow_delegation: true       # lives under `agent:`, never on the phase
    prompt_template: |
      Research from the previous phase:
      {{research}}

      Implement: $ARGUMENTS
      Commit, push, and open a PR against {{base_branch}} in this same phase.
```

### Workflow-level keys

| Key | Required | Notes |
|---|---|---|
| `id` | yes | Stable id. Also the key that decides whether a later install **updates** this workflow (see "Updating a Workflow"). |
| `name` | yes | |
| `description` | no | |
| `type` | no | `research`, `planning`, `implementation`, `review`, `deployment`, `custom` (default). NOT `workflow_type`. |
| `classification` | no | `simple`, `standard` (default), `complex`, `epic` |
| `repository` | no | `{url, ref}` default repo. `ref` defaults to `main`. |
| `repos` | no | List of default repo URLs for multi-repo workflows. |
| `requires_repos` | no | `false` for workflows that need no repository. Inferred when omitted. |
| `project_name` | no | |
| `inputs` | no | List of input declarations, see below. NOT `input_declarations`. |
| `phases` | yes | At least one. |
| `skills`, `claude_plugins` | no | Workflow-scope skill and Claude plugin refs. |

### Phase keys

| Key | Required | Notes |
|---|---|---|
| `id` | yes | NOT `phase_id`. Letters, digits, `.`, `_`, `-`; must start with a letter or digit. Unique. `{{<id>}}` substitutes this phase's output into later phases. |
| `name` | yes | |
| `order` | yes | Integer >= 1, unique. |
| `prompt_template` / `prompt_file` | set one | At most one: both together is rejected. Neither is accepted by the validator, but the phase then runs with no instructions, so always set one. `prompt_file` only resolves when installed as a package (see below). |
| `description`, `argument_hint`, `model` | no | Phase-level `model` wins over `agent.model`. |
| `execution_type` | no | Only `sequential` (the default). `parallel` and `human_in_loop` are **rejected**: neither is implemented. Omit the key. |
| `input_artifacts`, `output_artifacts` | no | Artifact TYPE names. Every `input_artifacts` entry must be produced by an earlier phase's `output_artifacts` or match a workflow input name, or the workflow is rejected. NOT `input_artifact_types` / `output_artifact_types` (those are the API's names, not YAML keys). |
| `timeout_seconds` | no | The lever for bounding a phase. |
| `allowed_tools` | no | Claude phases. On a codex phase a non-empty list is rejected. See "Choose the harness". |
| `clone_repos` | no | `false` skips the checkout for this phase (repo token and `{{repo_url}}` still provided). Default `true`. |
| `can_open_pr` | no | **Inert since #1478.** Still accepted so existing YAML loads, but it gates nothing. Do not add it to new workflows. Phase tokens carry `pull_requests: write` today; the agreed direction is that the PLATFORM opens the draft PR and agents go back to read-only on PRs, so do not build on the current permission either way (syntropic137/syntropic137#1492). |
| `delivers_repo_changes` | no | Default `true`. Set `false` on report-only phases (research, review, verify) so leftover build files do not fail the unpushed-work gate. |
| `agent` | no | `provider`, `model`, `allow_delegation`, `sandbox`. See below. |
| `skills`, `claude_plugins` | no | Phase-scope refs. |

`max_tokens` is **rejected**: no agent CLI has a token cap. Use `timeout_seconds`.

### Input keys

Each entry under `inputs` takes only `name`, `description`, `required` (default `true`), and `default`. The names `repository` and `repos` are **reserved and rejected**: repositories are passed with `-R owner/repo` at run time and reach the prompt as `{{repo_url}}`.

### Keys that are rejected, and what to write instead

| Rejected | Write instead |
|---|---|
| `phase_id` | `id` |
| `input_declarations` | `inputs` |
| `workflow_type` | `type` |
| `version` | nothing in the YAML. A version belongs to a package manifest, see "Updating a Workflow". |
| `output_artifact_types` / `input_artifact_types` | `output_artifacts` / `input_artifacts` |
| `allow_delegation` on a phase | `agent: { allow_delegation: true }` |
| `execution_type: parallel` / `human_in_loop` | omit `execution_type` |
| `max_tokens` | `timeout_seconds` |
| `agent.sandbox: read-only` | `agent.sandbox: workspace-write` |
| an input named `repository` / `repos` | `-R owner/repo` at run time, `{{repo_url}}` in prompts |

## Designing a Workflow

### 1. Choose the right pattern

Phases always run **one at a time, in `order`**. There is no parallel phase execution and no human approval gate inside a workflow.

| Pattern | Phases | Use When |
|---------|--------|----------|
| **RIPER-5** | 5 | Feature development, complex bug fixes: full Research, Innovate, Plan, Execute, Review loop |
| **Research, Analyze, Synthesize** | 3 | Investigation work, architectural questions |
| **Plan, then approve, then Execute** | 2 workflows | You want a human to approve the plan before any code is written |

RIPER-5 is the recommended default for implementation work. It runs straight through: nothing pauses for approval. If a human must approve before code is written, split it into two workflows: a planning workflow whose output you read, then an implementation workflow you run only after approving (`syn workflow run <impl-id> -t "<approved plan or its location>"`).

### 2. Declare your inputs

Every input a prompt uses must be declared under `inputs` (see the schema above). Declared inputs drive the CLI's missing-input check, the dashboard run form, and `{{name}}` substitution.

`task` is special: `-t/--task` on the CLI supplies it, and `$ARGUMENTS` and `{{task}}` both render it. Other inputs are supplied with `-i name=value`. Repositories are never inputs: pass `-R owner/repo`.

### 3. Wire phases with substitution

Each phase's `prompt_template` can reference:
- `$ARGUMENTS`: the task (`-t`)
- `{{name}}`: a declared input value
- `{{<phase-id>}}`: the output of an earlier phase, keyed by that phase's `id`
- `{{repo_url}}`, `{{execution_id}}`, `{{workflow_id}}`: built-ins

Keep the chain explicit: if phase 3 needs phase 1's output, reference `{{<phase-1-id>}}` directly rather than relying on phase 2 to pass it through.

### 4. Choose the harness, then right-size the model per phase

Harness selection lives in the workflow YAML, per phase. There is no CLI flag and no environment variable for it:

```yaml
phases:
  - id: implement
    name: Implement
    order: 1
    prompt_template: "Implement: $ARGUMENTS"
    agent:
      provider: claude          # claude | codex, claude is the default
      model: sonnet
  - id: review
    name: Review
    order: 2
    delivers_repo_changes: false
    prompt_template: "Review the change from the implement phase: {{implement}}"
    agent:
      provider: codex           # a different model reviews the work
      model: gpt-5.6-sol        # name a concrete model, see below
```

Rules that bite:

- **Codex phases need `CODEX_AUTH_JSON`** set in the platform `.env`. Without it, a phase declaring `provider: codex` fails to provision.
- **Name a concrete model id on every codex phase.** Codex does not report its model on the wire, so omitting `model` leaves the run **unpriced**: no cost lands in `syn costs` for that phase.
- **`agent.sandbox`: use `workspace-write` or omit it.** `workspace-write` is enforced least privilege on codex phases: codex may read, write and commit inside `/workspace` (including `artifacts/output/`) and nothing outside it, so it is the right level for review and verify phases. Omitted means `full-access`. `read-only` is rejected: it denies the `artifacts/output/` write a phase reports through. Claude ignores the field.
- **`allowed_tools` is enforced on claude phases** as the list of tools the agent has; anything not listed is unavailable. Names come from a closed set: `Bash`, `Edit`, `Glob`, `Grep`, `Read`, `Skill`, `Task`, `WebFetch`, `WebSearch`, `Write` (case-insensitive). An unknown name is rejected. Omit the key to keep every tool. On a **codex** phase a non-empty `allowed_tools` is rejected (an empty list is accepted and means nothing): codex has no tool vocabulary.
- **`allow_delegation: true`** (under `agent:`) stages both harnesses' credentials so the phase's agent can shell out one-shot to the other CLI. The deployment then needs credentials for both.
- **Claude-only features**: hook events, subagent tracking, TodoWrite, and Claude plugins. A phase that depends on any of them must run on claude.

The tier idea, a cheap model for shallow work and a capable model where reasoning depth matters, applies on both harnesses. Only the names differ:

- **claude phases** take Anthropic tier aliases. `haiku` for reading files, formatting output, simple classification. `sonnet` for most phases, balanced cost and capability. `opus` for complex implementation, architecture decisions, deep analysis.
- **codex phases** take a concrete OpenAI model id. There is no tier alias to fall back on, and leaving `model` out costs you the pricing data rather than saving money.

A well-designed RIPER-5 workflow might run claude/sonnet for Research, claude/opus for Innovate and Plan, claude/opus for Execute, and a codex Review phase with a named model and `delivers_repo_changes: false`, so a different model family certifies the work.

## Registering a Workflow

Validate first, then register. There are two ways to register, and they record different provenance:

```bash
syn workflow validate ./my-workflow.yaml             # a single file, or a package directory

# A. Single file, no version recorded
syn workflow create "My workflow" --from ./my-workflow.yaml

# B. Package directory, version recorded
syn workflow install ./my-workflow-package/          # local dir, git URL, org/repo, or marketplace name
```

`create --from` takes one `.yaml` file and cannot resolve `prompt_file:`; use inline `prompt_template`, or a package. `install` takes a directory (`workflow.yaml`, `workflows/*/workflow.yaml`, or loose `*.yaml` files, optionally with a `syntropic137-plugin.json` manifest), resolves `prompt_file`, and records the manifest `version` (or `0.0.0` when there is no manifest) plus the git commit for remote sources.

In both cases the workflow's YAML `id` becomes its platform id, so registering the same `id` again is an **update**, not a duplicate.

## Updating a Workflow In Place

Keep using the path you first registered with. Mixing them is what produces the provenance refusal.

**Registered with `syn workflow install`** (a version is recorded, `0.0.0` if the package has no manifest):

```bash
# Either bump "version" in syntropic137-plugin.json, then:
syn workflow install ./my-workflow-package/
# Or overwrite the same version on purpose:
syn workflow install ./my-workflow-package/ --force
# Git or marketplace sources: re-resolve and reinstall by package name
syn workflow update <package-name>                   # add --force to reinstall the same version
```

Reinstalling an unchanged definition reports "already installed" and writes nothing. Reinstalling the same version with a changed definition is refused until you bump the version or pass `--force`.

**Registered with `syn workflow create --from`** (no version recorded): re-run the same command. The workflow is updated in place.

**The refusal, and why it happens.** `Workflow '<id>' is installed with version 0.0.0, but this install declares no version. Refusing to overwrite recorded provenance with nothing.` means the workflow was registered with `syn workflow install` and you are now updating it with `syn workflow create --from`, which declares no version. `--force` does not bypass this. Do not add `version:` to the YAML (it is rejected as an unknown key); update through `syn workflow install <dir>` instead, as above. The same refusal names `source digest` when a workflow installed from a git source is reinstalled from a local path: reinstall from the git source (`syn workflow update <package-name>`).

To start clean instead, `syn workflow delete <id> --force` archives the template; it does not free the id for a provenance-free re-create, so prefer the update paths above.

## Common Mistakes

**Using key names from the API or older docs.** `phase_id`, `input_declarations`, `workflow_type`, `output_artifact_types`, and `version` are all rejected. See the rejected-keys table above.

**Phases referencing wrong substitution keys.** If phase 3 uses `{{phase_2}}` but phase 2's `id` is `analyze`, the substitution silently fails. Always match `{{<phase-id>}}` exactly to the phase's `id`.

**Every phase using the most capable model.** Costs scale fast with `opus` on claude phases, and with the top-tier model on codex phases. Audit your per-phase model assignments whenever a workflow runs expensive.

**A codex phase with no `model`.** It runs, and it reports no dollar cost, so the phase lands in `unpriced_tokens` rather than in your cost total. The spend is real and your reported total is short. Always name a concrete model id on codex phases.

**Declaring `read-only` for a reviewer.** It looks like the safe choice and is rejected: it denies the `artifacts/output/` write the reviewer reports through. Use `agent.sandbox: workspace-write`, which keeps the reviewer's writes inside `/workspace`.

**Missing `inputs` for values used in prompts.** If `{{base_branch}}` appears in a prompt but isn't declared, it won't be substituted. Validate the workflow before registering.

**Splitting git operations across phases.** If phase 1 commits code and phase 2 tries to push or open a PR, phase 2 will start with a clean workspace and find nothing to push. All git operations, including commit, push, and `gh pr create`, must happen in the same phase that wrote the changes. If the workflow design requires separating research/implementation from the git step, have the implementation phase output a patch artifact and have the git phase apply it in a fresh clone.

**Expecting an approval gate.** No phase pauses for a human. Any workflow that writes, commits, or deploys and needs sign-off should be split so the human reviews the output of one workflow before running the next.

## Escalation Point

If a workflow design isn't working as expected after two attempts (phases not receiving outputs, models ignoring injected context), **stop and inspect the execution detail** before redesigning. Run `syn control status <exec-id>` and check each phase's `artifact_id`. The artifact content will tell you exactly what was passed forward.

## Integration

Design here, run with execution-control, then monitor with observability. Install community workflows via the marketplace skill instead of building from scratch.

## CLI Quick Reference

```bash
syn workflow list
syn workflow show <id>
syn workflow validate ./my-workflow.yaml
syn workflow create "My workflow" --from ./my-workflow.yaml   # register or update a single file
syn workflow install ./my-package/ [--force]                 # register or update a package
syn workflow run <id> --task "Implement retry logic" -R owner/repo
syn workflow run <id> -t "Fix auth bug" -R owner/repo -i base_branch=develop
syn workflow delete <id> --force
```
