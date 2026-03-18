# Organization Management — Syntropic137

Use this knowledge when the user wants to manage organizations, systems, and repositories — the structural hierarchy for tracking health, costs, and patterns across their projects.

## Organization Hierarchy

```
Organization (top-level entity, e.g., "Syntropic137")
  └── System (logical grouping, e.g., "Backend", "Frontend", "Infrastructure")
       └── Repo (registered GitHub repository)
```

This hierarchy enables:
- **Cost rollup** — see spend by system or org
- **Health monitoring** — system-level health across all repos
- **Pattern analysis** — execution trends per system
- **Contribution heatmaps** — team activity across repos

## Organizations

```bash
# List organizations
curl -s http://localhost:8000/organizations | python -m json.tool

# Create organization
curl -X POST http://localhost:8000/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Syntropic137", "slug": "syn137"}'

# Get organization detail
curl -s http://localhost:8000/organizations/<org-id> | python -m json.tool

# Update
curl -X PUT http://localhost:8000/organizations/<org-id> \
  -d '{"name": "New Name"}'

# Delete (soft delete — cannot update/delete again after)
curl -X DELETE http://localhost:8000/organizations/<org-id>
```

### Domain Model

- **Aggregate**: `OrganizationAggregate`
- **State**: `name`, `slug`, `created_by`, `created_at`, `is_deleted`
- **Events**: `OrganizationCreatedEvent`, `OrganizationUpdatedEvent`, `OrganizationDeletedEvent`
- **Invariant**: Cannot update or delete if already deleted

## Systems

Systems group related repos for monitoring and cost analysis.

```bash
# List systems in an org
curl -s "http://localhost:8000/systems?organization_id=<org-id>" | python -m json.tool

# Create system
curl -X POST http://localhost:8000/systems \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "<org-id>",
    "name": "Backend Services",
    "description": "API and domain services"
  }'

# Get system detail (includes health, cost data)
curl -s http://localhost:8000/systems/<system-id> | python -m json.tool

# Get system health status
curl -s http://localhost:8000/systems/<system-id>/status | python -m json.tool

# Get system cost
curl -s http://localhost:8000/systems/<system-id>/cost | python -m json.tool
```

### Domain Model

- **Aggregate**: `SystemAggregate`
- **State**: `organization_id`, `name`, `description`, `created_by`, `is_deleted`
- **Events**: `SystemCreatedEvent`, `SystemUpdatedEvent`, `SystemDeletedEvent`
- **Invariant**: Linked to parent organization

## Repositories

Repos are registered from GitHub App installations and can be assigned to systems.

```bash
# List repos
curl -s "http://localhost:8000/repos?organization_id=<org-id>" | python -m json.tool

# Register repo (usually automatic via GitHub App)
curl -X POST http://localhost:8000/repos \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "<org-id>",
    "provider": "github",
    "provider_repo_id": "123456",
    "full_name": "syntropic137/syntropic137",
    "owner": "syntropic137",
    "default_branch": "main",
    "installation_id": "<installation-id>"
  }'

# Assign repo to system
curl -X POST http://localhost:8000/repos/<repo-id>/assign \
  -d '{"system_id": "<system-id>"}'

# Unassign from system (must unassign before reassigning)
curl -X POST http://localhost:8000/repos/<repo-id>/unassign
```

### Domain Model

- **Aggregate**: `RepoAggregate`
- **State**: `organization_id`, `system_id`, `provider`, `provider_repo_id`, `full_name`, `owner`, `default_branch`, `installation_id`, `is_private`
- **Events**: `RepoRegisteredEvent`, `RepoAssignedToSystemEvent`, `RepoUnassignedFromSystemEvent`
- **Invariant**: Can only assign once — must unassign first to reassign

## Read Models (Projections)

The organization context has rich read models for operational intelligence:

| Read Model | Purpose | Query |
|-----------|---------|-------|
| `GlobalOverview` | Cross-org overview with cost rollup | `GET /organizations/overview` |
| `SystemStatus` | Per-system health (healthy/degraded/failing) | `GET /systems/{id}/status` |
| `SystemPatterns` | Execution patterns and trends | `GET /systems/{id}/patterns` |
| `SystemCost` | System-level cost aggregation | `GET /systems/{id}/cost` |
| `ContributionHeatmap` | Team contribution patterns | `GET /insights/heatmap` |

## Seeding Data

For development, seed sample org/system/repo data:

```bash
just seed-organization    # Seed org, system, repos
just seed-all             # Seed everything (workflows + triggers + org)
```

## Common Scenarios

### "Track costs across my backend services"

1. Create an organization
2. Create a "Backend" system
3. Register repos and assign to the system
4. View system cost: `GET /systems/<id>/cost`

### "See health across all my repos"

1. Ensure repos are registered and assigned to systems
2. Check system status: `GET /systems/<id>/status` — shows healthy/degraded/failing per repo
3. Global overview: `GET /organizations/overview` — cross-org summary
