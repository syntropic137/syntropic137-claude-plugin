# Workflow Management — Syntropic137

Use this knowledge when the user wants to create, configure, inspect, or manage workflows. Workflows are the core unit of work in Syntropic137 — they define multi-phase agent execution pipelines.

## Core Concepts

### Workflows as Claude Code Commands (ISS-211)

Workflows follow the **Claude Code command standard**:
- **`$ARGUMENTS`** in phase prompts is replaced with the task description at runtime
- **`{{variable}}`** for named inputs declared in `input_declarations`
- **`{{phase-id}}`** inline substitution — replaced with the output of a previous phase (e.g., `{{discovery}}` → output from the "discovery" phase)
- **`{{repository}}`** in `repository.url` enables runtime repo override via `--input repository=owner/repo`

This means workflows are reusable — the same template works for any task/repo.

### Workflow Templates vs Executions

A **workflow template** is a reusable definition — like a class. A **workflow execution** is a running instance — like an object. One template can have many concurrent executions.

### Workflow Types

| Type | Purpose |
|------|---------|
| `research` | Information gathering, analysis |
| `planning` | Architecture, design, strategy |
| `implementation` | Code writing, feature development |
| `review` | Code review, PR analysis |
| `deployment` | Release, deploy, rollback |
| `custom` | Anything else |

### Workflow Classification (Complexity)

| Classification | Phases | Typical Duration |
|---------------|--------|-----------------|
| `simple` | 1-2 | Minutes |
| `standard` | 2-4 | 10-30 min |
| `complex` | 4-8 | 30-120 min |
| `epic` | 8+ | Hours |

### Input Declarations

Workflows declare their expected inputs at the template level:

```yaml
input_declarations:
  - name: task
    description: "The task to perform"
    required: true
  - name: repository
    description: "Target repository (owner/repo)"
    required: false
    default: "syntropic137/syntropic137"
  - name: branch
    description: "Git branch to work on"
    required: false
    default: "main"
```

At runtime, these map to:
- **`task`** → `--task` / `-t` CLI flag, or `$ARGUMENTS` in prompts
- **Named inputs** → `--input key=value` CLI flags, or `{{key}}` in prompts

The dashboard auto-generates input forms from `input_declarations`.

### Phase Definitions

Each phase in a workflow template defines:

```yaml
phase_id:       Unique identifier (e.g., "analyze", "implement", "review")
name:           Human-readable name
order:          Execution order (0-based)
execution_type: SEQUENTIAL (default), PARALLEL, HUMAN_IN_LOOP
description:    What this phase does
prompt_template: The prompt text — use $ARGUMENTS, {{variable}}, {{phase-id}}
argument_hint:  Describes what $ARGUMENTS expects (for docs/UI)
model:          Per-phase model override (e.g., "sonnet", "opus")
input_artifact_types:  What artifacts this phase consumes
output_artifact_types: What artifacts this phase produces
allowed_tools:  Which tools the agent can use
max_tokens:     Token limit for agent response
timeout_seconds: Phase timeout
```

### Prompt Substitution Order

When a phase executes, its prompt template is resolved in this order:

1. **Built-in variables** — system-provided context
2. **Named inputs** — `{{variable}}` replaced with runtime input values
3. **`$ARGUMENTS`** — replaced with the `task` field from the execution request
4. **Phase outputs** — `{{phase-id}}` replaced with the output artifact of that phase

### Agent Configuration (per phase)

```yaml
provider:        "claude" (default) or "openai" (mock only in tests)
model:           "sonnet" (default), "haiku", "opus" — per-phase override
max_tokens:      4096 (default)
temperature:     0.7 (default)
timeout_seconds: 300 (default)
allowed_tools:   () (empty = all tools)
```

The `model` field on a phase overrides the default model — use cheaper models for simple phases (haiku for analysis) and more capable models for complex phases (opus for implementation).

## How to Create a Workflow

### Via YAML (Recommended)

Workflows are defined in YAML files in `workflows/examples/`. Here's a research workflow using the CC command standard:

```yaml
name: Research Workflow
description: "Multi-phase research with discovery, deep analysis, and synthesis"
workflow_type: research
classification: standard

repository:
  url: "https://github.com/{{repository}}"
  ref: main

input_declarations:
  - name: task
    description: "The research topic or question to investigate"
    required: true
  - name: topic
    description: "Optional focus area to narrow the research"
    required: false

phases:
  - phase_id: discovery
    name: "Discovery"
    order: 0
    argument_hint: "<research topic or question>"
    model: sonnet
    prompt_template: |
      You are a research agent. Your task:

      $ARGUMENTS

      Explore the codebase, documentation, and relevant sources.
      Produce a structured discovery report.
    output_artifact_types: [analysis]
    timeout_seconds: 300

  - phase_id: deep_dive
    name: "Deep Dive Analysis"
    order: 1
    model: opus
    prompt_template: |
      Based on the discovery phase findings:

      {{discovery}}

      Perform deep analysis. Examine edge cases, trade-offs, and alternatives.
    input_artifact_types: [analysis]
    output_artifact_types: [analysis]
    timeout_seconds: 600

  - phase_id: synthesis
    name: "Synthesis & Documentation"
    order: 2
    model: sonnet
    prompt_template: |
      Original task: $ARGUMENTS

      Discovery findings: {{discovery}}
      Deep analysis: {{deep_dive}}

      Synthesize everything into a clear, actionable report.
    input_artifact_types: [analysis]
    output_artifact_types: [documentation]
    timeout_seconds: 300
```

**Key patterns in this example:**
- `$ARGUMENTS` carries the task description into phases 1 and 3
- `{{discovery}}` and `{{deep_dive}}` reference previous phase outputs
- `{{repository}}` in the URL allows runtime repo override
- `model: opus` on the deep dive phase uses a more capable model where it matters
- `input_declarations` tells the CLI/dashboard what inputs to collect

### Via CLI

```bash
# Validate a YAML definition
uv run --package syn-cli syn workflow validate ./my-workflow.yaml

# Create from YAML (seeded at startup)
just seed-workflows

# Basic creation via CLI flags
uv run --package syn-cli syn workflow create "Fix Bug in Auth Service" \
  --type implementation \
  --repo syntropic137/syntropic137 \
  --description "Analyze the bug, implement a fix, and review the changes"

# Run with --task flag (maps to $ARGUMENTS)
uv run --package syn-cli syn workflow run <workflow-id> \
  --task "Investigate the auth middleware timeout bug" \
  --input repository=syntropic137/syntropic137

# Short form
uv run --package syn-cli syn run <workflow-id> -t "Fix the login regression"
```

### Via API

```bash
# Create workflow template
curl -X POST http://localhost:8137/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fix Bug in Auth Service",
    "workflow_type": "implementation",
    "classification": "standard",
    "repository_url": "https://github.com/{{repository}}",
    "repository_ref": "main",
    "description": "Analyze the bug, implement a fix, and review the changes",
    "input_declarations": [
      {"name": "task", "description": "Bug to fix", "required": true},
      {"name": "repository", "description": "Target repo", "required": false, "default": "syntropic137/syntropic137"}
    ],
    "phases": [
      {
        "phase_id": "analyze",
        "name": "Bug Analysis",
        "order": 0,
        "model": "sonnet",
        "argument_hint": "<bug description or issue URL>",
        "prompt_template": "Analyze the bug: $ARGUMENTS\n\nIdentify root cause and affected code.",
        "output_artifact_types": ["analysis"],
        "timeout_seconds": 300
      },
      {
        "phase_id": "implement",
        "name": "Implementation",
        "order": 1,
        "model": "opus",
        "prompt_template": "Based on the analysis:\n\n{{analyze}}\n\nImplement a fix. Write tests.",
        "input_artifact_types": ["analysis"],
        "output_artifact_types": ["code"],
        "timeout_seconds": 600
      },
      {
        "phase_id": "review",
        "name": "Code Review",
        "order": 2,
        "model": "sonnet",
        "prompt_template": "Review the implementation:\n\n{{implement}}\n\nCheck correctness, style, and test coverage.",
        "input_artifact_types": ["code"],
        "output_artifact_types": ["review"],
        "timeout_seconds": 300
      }
    ]
  }'

# Execute with task
curl -X POST http://localhost:8137/workflows/<workflow-id>/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fix the auth middleware timeout when tokens expire",
    "inputs": {"repository": "syntropic137/syntropic137"}
  }'
```

## How to List and Inspect Workflows

```bash
# List all workflow templates
uv run --package syn-cli syn workflow list

# Show template details (phases, config)
uv run --package syn-cli syn workflow show <workflow-id>

# List execution runs for a workflow
curl -s http://localhost:8137/workflows/<workflow-id>/runs | python -m json.tool
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/workflows` | List all templates (paginated) |
| `GET` | `/workflows/{id}` | Get template detail with phases |
| `GET` | `/workflows/{id}/runs` | List execution runs for template |
| `POST` | `/workflows` | Create new template |

### Response Shape

```json
{
  "id": "wf-abc123",
  "name": "Fix Bug in Auth Service",
  "description": "...",
  "workflow_type": "implementation",
  "classification": "standard",
  "input_declarations": [
    {"name": "task", "description": "Bug to fix", "required": true, "default": null},
    {"name": "repository", "description": "Target repo", "required": false, "default": "syntropic137/syntropic137"}
  ],
  "phases": [
    {
      "phase_id": "analyze",
      "name": "Bug Analysis",
      "order": 0,
      "execution_type": "SEQUENTIAL",
      "argument_hint": "<bug description or issue URL>",
      "model": "sonnet",
      "prompt_template": "...",
      "output_artifact_types": ["analysis"],
      "timeout_seconds": 300
    }
  ],
  "created_at": "2026-03-18T10:00:00Z",
  "runs_count": 5
}
```

## Workflow Design Patterns

### Pattern: RIPER-5 (Research → Innovate → Plan → Execute → Review)

The most thorough workflow for feature development (see `implementation.yaml` example):

1. **Research** (sonnet) — Read-only codebase exploration. `$ARGUMENTS` for the task.
2. **Innovate** (opus) — Brainstorm approaches. `{{research}}` for context.
3. **Plan** (opus, HUMAN_IN_LOOP) — Detailed spec. Pauses for user approval.
4. **Execute** (opus) — Implement changes per approved plan. `{{plan}}` for spec.
5. **Review** (sonnet) — Validate against plan. `{{plan}}` + `{{execute}}` for context.

Each phase references previous outputs via `{{phase-id}}`. Per-phase model selection optimizes cost.

### Pattern: Research → Analyze → Synthesize

Lighter pattern for investigation work (see `research.yaml` example):

1. **Discovery** (sonnet) — Initial exploration using `$ARGUMENTS`
2. **Deep Dive** (opus) — Thorough analysis using `{{discovery}}`
3. **Synthesis** (sonnet) — Consolidate findings, `$ARGUMENTS` + `{{discovery}}` + `{{deep_dive}}`

### Pattern: Parallel Analysis

For broad codebase analysis, use PARALLEL execution type:

- Phase 1: Analyze frontend (parallel)
- Phase 1: Analyze backend (parallel)
- Phase 1: Analyze infrastructure (parallel)
- Phase 2: Synthesize findings (sequential, depends on all phase 1 outputs)

### Pattern: Human-in-the-Loop

For workflows requiring approval gates:

- Phase 1: Generate proposal (agent)
- Phase 2: Review proposal (HUMAN_IN_LOOP — pauses for user input)
- Phase 3: Implement approved changes (agent)

## Domain Model (for advanced users)

### Event Flow

```
CreateWorkflowTemplateCommand
  → WorkflowTemplateAggregate.create_workflow()
    → WorkflowTemplateCreatedEvent
      → WorkflowDetailProjection (read model for listing/detail)
```

### Key Aggregate: WorkflowTemplateAggregate

- **Status**: PENDING → IN_PROGRESS → COMPLETED | FAILED | CANCELLED
- **Immutable after creation**: Templates are versioned through new templates, not mutations
- **Aggregate ID**: workflow_id

### Projections

- **WorkflowDetailProjection** (`workflow_details`): Template definitions + `runs_count`
- Updated by: `WorkflowTemplateCreatedEvent`, `WorkflowExecutionStartedEvent` (increments runs_count)
