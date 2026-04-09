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

## The Core Model: Templates vs Executions

A **workflow template** is a reusable definition (like a class). A **workflow execution** is a running instance (like an object). One template can have many concurrent executions with different tasks, repos, and inputs.

Templates define **phases**: each phase is one Claude CLI invocation in its own workspace. Phases run sequentially by default; outputs from phase N feed into phase N+1 via `{{phase-id}}` substitution.

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

### 4. Right-size the model per phase

Use cheaper models for read-only, exploratory phases; use more capable models where reasoning depth matters:

- **haiku**: reading files, formatting output, simple classification
- **sonnet**: most phases, balanced cost/capability
- **opus**: complex implementation, architecture decisions, deep analysis

A well-designed RIPER-5 workflow might use sonnet for Research, opus for Innovate and Plan, opus for Execute, sonnet for Review.

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

**Every phase using opus.** Costs scale fast with opus. Audit your model assignments whenever a workflow runs expensive.

**Missing `input_declarations` for inputs used in prompts.** If `{{repository}}` appears in a prompt but isn't declared, it won't be substituted. Validate the workflow before registering.

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
