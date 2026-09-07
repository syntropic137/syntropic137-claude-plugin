---
name: workflow-management
description: Create, configure, and manage Syntropic137 workflow templates (phase definitions, agent config, YAML schema, $ARGUMENTS substitution, input declarations, and design patterns like RIPER-5)
---

# Workflow Management: Syntropic137

When you need to build a new automated workflow, or understand why an existing one behaves unexpectedly, start here. Workflows are the core unit of work: YAML-defined multi-phase agent pipelines that run in isolated Docker workspaces.

**NEVER hardcode task descriptions or repository names into phase prompts.** Use `$ARGUMENTS` for the task and `{{repository}}` in the URL so the same template works for any repo and any task.

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

Templates define **phases**: each phase is one headless agent invocation in its own workspace, on whichever harness that phase declares. Phases run sequentially by default, and outputs from phase N feed into phase N+1 via `{{phase-id}}` substitution.

**Phase workspaces are ephemeral.** Each phase starts in a fresh Docker container: no git branches, staged files, commits, or file changes from a prior phase carry over. The only thing that crosses a phase boundary is the artifact output. If a phase needs to do git work (commit, push, `gh pr create`), it must do so in the same phase that made the changes. If a later phase needs those changes, either collapse the phases or have the earlier phase output a patch/diff artifact that the later phase applies.

## Designing a Workflow: 4 Phases

### 1. Choose the right pattern

Pick based on complexity:

| Pattern | Phases | Use When |
|---------|--------|----------|
| **RIPER-5** | 5 | Feature development, complex bug fixes: full Research→Innovate→Plan→Execute→Review loop |
| **Research→Analyze→Synthesize** | 3 | Investigation work, architectural questions |
| **Parallel Analysis** | 2 | Broad codebase surveys: frontend/backend/infra simultaneously |
| **Human-in-the-Loop** | 3+ | Any workflow requiring approval before execution |

RIPER-5 is the recommended default for implementation work. It has a `HUMAN_IN_LOOP` gate at the Plan phase: the agent pauses and waits for your approval before writing any code.

### 2. Define your input declarations

Every input the workflow needs must be declared in `input_declarations`. This drives the CLI flags, the dashboard UI, and the `{{variable}}` substitution in prompts:

```yaml
input_declarations:
  - name: task
    description: "What to implement or fix"
    required: true
  - name: repository
    description: "owner/repo"
    required: false
    default: "syntropic137/syntropic137"
```

`task` maps to `$ARGUMENTS` and the `--task` flag. Named inputs map to `{{name}}` in prompts and `--input name=value` on the CLI.

### 3. Wire phases with substitution

Each phase's `prompt_template` can reference:
- `$ARGUMENTS`: the task description
- `{{variable}}`: a declared input value
- `{{phase-id}}`: the output artifact from a previous phase

Phase outputs chain forward automatically. Keep the substitution chain explicit: if phase 3 needs phase 1's output, reference `{{phase-1-id}}` directly rather than relying on phase 2 to pass it through.

### 4. Choose the harness, then right-size the model per phase

Harness selection lives in the workflow YAML, per phase. There is no CLI flag and no environment variable for it:

```yaml
phases:
  - id: implement
    agent:
      provider: claude          # claude | codex, claude is the default
      model: sonnet
  - id: review
    agent:
      provider: codex           # a different model reviews the work
      model: gpt-5.6-sol        # name a concrete model, see below
      sandbox: read-only        # codex honours this, claude does not
```

Rules that bite:

- **Codex phases need `CODEX_AUTH_JSON`** set in the platform `.env`. Without it, a phase declaring `provider: codex` fails to provision.
- **Name a concrete model id on every codex phase.** Codex does not report its model on the wire, so omitting `model` leaves the run **unpriced**: no cost lands in `syn costs` for that phase.
- **`allowed_tools` restricts nothing on either harness.** Per ADR-069 the platform never populates it, so no tool policy is applied and the codex-side guard is unreachable. Declare it to document intent. To bound a phase, put it on codex and set `sandbox`, which limits filesystem writes only: network egress is available at every level, and a phase publishing under `artifacts/output/` needs `full-access`.
- **`sandbox` constrains codex only** today. The levels are `read-only`, `workspace-write`, and `full-access`. Declaring `read-only` on a claude phase does not restrict it, so do not read it as a guarantee there.
- **Claude-only features**: hook events, subagent tracking, TodoWrite, and Claude plugins. A phase that depends on any of them must run on claude.

The tier idea, a cheap model for shallow work and a capable model where reasoning depth matters, applies on both harnesses. Only the names differ:

- **claude phases** take Anthropic tier aliases. `haiku` for reading files, formatting output, simple classification. `sonnet` for most phases, balanced cost and capability. `opus` for complex implementation, architecture decisions, deep analysis.
- **codex phases** take a concrete OpenAI model id. There is no tier alias to fall back on, and leaving `model` out costs you the pricing data rather than saving money.

A well-designed RIPER-5 workflow might run claude/sonnet for Research, claude/opus for Innovate and Plan, claude/opus for Execute, and a codex Review phase with a named model and `sandbox: read-only` so the verifier cannot modify what it certifies.

## Creating a Workflow

Validate first, then register:

```bash
syn workflow validate ./my-workflow.yaml
syn workflow create --type implementation --repo owner/repo --description "..."
```

Or load from the source repo: `just seed-workflows` loads all YAML files from `workflows/examples/`.

See `workflow-management` skill for full YAML schema reference including `allowed_tools`, `timeout_seconds`, `execution_type: PARALLEL`, and API-based creation.

## Common Mistakes

**Phases referencing wrong substitution keys.** If phase 3 uses `{{phase_2}}` but phase 2's `phase_id` is `analyze`, the substitution silently fails. Always match `{{phase-id}}` exactly to the `phase_id` field.

**Every phase using the most capable model.** Costs scale fast with `opus` on claude phases, and with the top-tier model on codex phases. Audit your per-phase model assignments whenever a workflow runs expensive.

**A codex phase with no `model`.** It runs, and it reports no dollar cost, so the phase lands in `unpriced_tokens` rather than in your cost total. The spend is real and your reported total is short. Always name a concrete model id on codex phases.

**Treating `allowed_tools` as a control.** Per ADR-069 the platform never populates it, so it restricts nothing on either harness and syntropic137#803 tracks the gap. Declare it to document intent. To actually bound a phase, put it on `codex` and set `sandbox: read-only`.

**Missing `input_declarations` for inputs used in prompts.** If `{{repository}}` appears in a prompt but isn't declared, it won't be substituted. Validate the workflow before registering.

**Splitting git operations across phases.** If phase 1 commits code and phase 2 tries to push or open a PR, phase 2 will start with a clean workspace and find nothing to push. All git operations, including commit, push, and `gh pr create`, must happen in the same phase that wrote the changes. If the workflow design requires separating research/implementation from the git step, have the implementation phase output a patch artifact and have the git phase apply it in a fresh clone.

**Skipping HUMAN_IN_LOOP on destructive workflows.** Any workflow that writes, commits, or deploys should pause for human review. Automation without oversight is how you get force-pushed to main at 2am.

## Escalation Point

If a workflow design isn't working as expected after two attempts (phases not receiving outputs, models ignoring injected context), **stop and inspect the execution detail** before redesigning. Run `syn control status <exec-id>` and check each phase's `artifact_id`. The artifact content will tell you exactly what was passed forward.

## Integration

Design here, run with execution-control, then monitor with observability. Install community workflows via the marketplace skill instead of building from scratch.

## CLI Quick Reference

```bash
syn workflow list
syn workflow show <id>
syn workflow validate ./my-workflow.yaml
syn workflow run <id> --task "Implement retry logic"
syn workflow run <id> --task "Fix auth bug" --input repository=owner/repo
syn workflow delete <id>
```
