# Syntropic137 Claude Code Plugin

A Claude Code plugin for setting up, observing, and operating the [Syntropic137](https://github.com/syntropic137/syntropic137) AI agent workflow engine.

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

The plugin wraps the `syn` CLI and `just` task runner to give you a conversational interface to the Syntropic137 platform:

- **Setup commands** use `just` recipes for infrastructure operations
- **Operational commands** delegate to `uv run --package syn-cli syn <command>`
- **Session start hook** checks API reachability and notifies you if the platform is down

## Skills

The plugin includes a `platform-ops` skill that provides Claude with architecture context, service maps, and troubleshooting recipes. This is automatically available when the plugin is installed — no need to invoke it directly.

## Development

This plugin is developed as a submodule at `lib/syntropic137-claude-plugin` in the [syntropic137](https://github.com/syntropic137/syntropic137) monorepo. To work on it:

```bash
cd lib/syntropic137-claude-plugin
# Make changes
# Test with: claude plugin install . --scope project
```

## License

MIT
