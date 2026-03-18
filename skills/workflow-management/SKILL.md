# Workflow Management — Syntropic137

Use this knowledge when the user wants to create, configure, inspect, or manage workflows. Workflows are the core unit of work in Syntropic137 — they define multi-phase agent execution pipelines.

## Core Concepts

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

### Phase Definitions

Each phase in a workflow template defines:

```
phase_id:       Unique identifier (e.g., "analyze", "implement", "review")
name:           Human-readable name
order:          Execution order (0-based)
execution_type: SEQUENTIAL (default), PARALLEL, HUMAN_IN_LOOP
description:    What this phase does
prompt_template: The actual prompt text for the agent
input_artifact_types:  What artifacts this phase consumes
output_artifact_types: What artifacts this phase produces
allowed_tools:  Which tools the agent can use
max_tokens:     Token limit for agent response
timeout_seconds: Phase timeout
```

### Agent Configuration (per phase)

```
provider:        "claude" (default) or "openai" (mock only in tests)
model:           "haiku", "sonnet", "opus" (CLI aliases)
max_tokens:      4096 (default)
temperature:     0.7 (default)
timeout_seconds: 300 (default)
allowed_tools:   () (empty = all tools)
```

### Phase Inputs

Phases can reference outputs from previous phases:

```
inputs:
  - source: "previous_phase_id"
    artifact_type: "code"
  - source: "user"
    key: "issue_url"
```

## How to Create a Workflow

### Via CLI

```bash
# Basic creation
uv run --package syn-cli syn workflow create "Fix Bug in Auth Service" \
  --type implementation \
  --repo syntropic137/syntropic137 \
  --description "Analyze the bug, implement a fix, and review the changes"

# With specific branch
uv run --package syn-cli syn workflow create "Research Caching Strategy" \
  --type research \
  --repo syntropic137/syntropic137 \
  --ref feat/caching \
  --description "Evaluate caching options for the API layer"

# Validate a YAML definition before creating
uv run --package syn-cli syn workflow validate ./my-workflow.yaml
```

### Via API

```bash
# Create workflow template
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fix Bug in Auth Service",
    "workflow_type": "implementation",
    "classification": "standard",
    "repository_url": "https://github.com/syntropic137/syntropic137",
    "repository_ref": "main",
    "description": "Analyze the bug, implement a fix, and review the changes",
    "phases": [
      {
        "phase_id": "analyze",
        "name": "Bug Analysis",
        "order": 0,
        "prompt_template": "Analyze the bug described in {issue_url}. Identify root cause and affected code.",
        "output_artifact_types": ["analysis"],
        "timeout_seconds": 300
      },
      {
        "phase_id": "implement",
        "name": "Implementation",
        "order": 1,
        "prompt_template": "Based on the analysis, implement a fix. Write tests.",
        "input_artifact_types": ["analysis"],
        "output_artifact_types": ["code"],
        "timeout_seconds": 600
      },
      {
        "phase_id": "review",
        "name": "Code Review",
        "order": 2,
        "prompt_template": "Review the implementation for correctness, style, and test coverage.",
        "input_artifact_types": ["code"],
        "output_artifact_types": ["review"],
        "timeout_seconds": 300
      }
    ]
  }'
```

## How to List and Inspect Workflows

```bash
# List all workflow templates
uv run --package syn-cli syn workflow list

# Show template details (phases, config)
uv run --package syn-cli syn workflow show <workflow-id>

# List execution runs for a workflow
curl -s http://localhost:8000/workflows/<workflow-id>/runs | python -m json.tool
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
  "phases": [
    {
      "phase_id": "analyze",
      "name": "Bug Analysis",
      "order": 0,
      "execution_type": "SEQUENTIAL",
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

### Pattern: Research → Plan → Implement → Review

The most common workflow for feature development:

1. **Research** — Gather context, analyze requirements, identify affected code
2. **Plan** — Design approach, identify files to change, write pseudocode
3. **Implement** — Write code, write tests
4. **Review** — Self-review for correctness, style, coverage

Each phase produces artifacts consumed by the next. The aggregate enforces ordering.

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
