# Syntropic137 Claude Code Plugin

Turn Claude Code into your Syntropic137 orchestration brain. Create workflows, kick off executions, monitor costs, troubleshoot issues — all through natural conversation.

## Installation

**From GitHub (marketplace):**

```bash
claude plugin marketplace add syntropic137/syntropic137-claude-plugin
claude plugin install syntropic
```

**From local clone (development):**

```bash
claude plugin install ./lib/syntropic137-claude-plugin --scope project
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [just](https://github.com/casey/just) — task runner
- [Node.js](https://nodejs.org/) + [pnpm](https://pnpm.io/) — for the dashboard

Don't worry about remembering these — `/syn-setup` checks everything for you.

## Getting Started

```
/syn-setup
```

That's it. The setup wizard detects your environment, reports what's working and what's missing, then walks you through fixing each issue step by step.

## Commands

| Command | Description |
|---------|-------------|
| `/syn-setup` | Guided platform bootstrap — detect, report, fix |
| `/syn-status` | Composite view: containers + health + metrics |
| `/syn-health` | API health check with diagnostics |
| `/syn-costs [summary \| session <id> \| workflow <id>]` | Cost tracking |
| `/syn-sessions [list \| show <id>]` | Session listing and details |
| `/syn-metrics [--workflow <id>]` | Aggregated metrics |
| `/syn-observe <session-id> [events \| tools \| errors]` | Observability data |

## How It Works

The plugin combines **slash commands** for quick actions with **deep skill knowledge** that lets Claude Code understand and operate the entire Syntropic137 platform intelligently.

- **Commands** — Quick entry points for common operations (delegate to `syn` CLI and `just` recipes)
- **Skills** — Deep domain knowledge that Claude uses to reason about your platform (see below)
- **Hook** — Session start connectivity check, so Claude knows if the platform is up

## Skills (Domain Knowledge)

Skills give Claude deep understanding of the system. They're automatically loaded when relevant — you don't invoke them directly. Claude uses this knowledge to answer questions, suggest approaches, and troubleshoot issues.

| Skill | What Claude Learns |
|-------|-------------------|
| **workflow-management** | Creating workflows as CC commands: `$ARGUMENTS`, `{{variable}}`, `{{phase-id}}` substitution. Input declarations, per-phase model overrides, YAML schema, RIPER-5 and research patterns. |
| **execution-control** | Running workflows (`--task`), monitoring progress, control plane (pause/resume/cancel/inject), Processor To-Do List internals, troubleshooting failures. |
| **observability** | Sessions, tool timelines, token metrics, cost breakdowns. Two-lane architecture. How to interpret "why was this expensive?" or "why did this fail?" |
| **organization** | Org→System→Repo hierarchy, cost rollup, health monitoring, contribution heatmaps. |
| **github-automation** | GitHub App setup, webhook trigger rules with safety limits, input mapping from webhooks to workflow inputs, Smee/Cloudflare webhook delivery. |
| **setup** | 14-stage onboarding wizard, 1Password vault integration, Cloudflare tunnels, Docker Compose variants, 100+ justfile recipes, secrets management, troubleshooting. |
| **platform-ops** | Service map with ports, workspace management, token injection security (Envoy proxy), QA/testing commands, infrastructure troubleshooting recipes. |

### What this means in practice

Instead of memorizing CLI commands, just tell Claude what you want:

- *"Create a workflow that reviews PRs on my backend repo"* → Claude uses workflow-management + github-automation skills
- *"Why did execution exec-abc123 fail?"* → Claude uses execution-control + observability skills
- *"Set up automatic triggers for when issues are opened"* → Claude uses github-automation skill
- *"The API is down, help me fix it"* → Claude uses platform-ops skill
- *"Help me set up 1Password for secrets"* → Claude uses setup skill
- *"How do I deploy with Cloudflare tunnel?"* → Claude uses setup skill

## Development

This plugin is developed as a submodule at `lib/syntropic137-claude-plugin` in the [syntropic137](https://github.com/syntropic137/syntropic137) monorepo. To work on it:

```bash
cd lib/syntropic137-claude-plugin
# Make changes
# Test with: claude plugin install . --scope project
```

## License

MIT
