---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | search <query> | install <plugin> | add <registry>]"
---

# /syn-marketplace — Marketplace & Workflow Installation

First, detect the CLI:

```bash
if command -v syn &>/dev/null; then
    SYN_CLI="syn"
elif command -v uv &>/dev/null; then
    SYN_CLI="uv run --package syn-cli syn"
else
    SYN_CLI=""
fi
```

Parse the user's argument:

- No argument or `list` → list registered marketplaces
  - If SYN_CLI: `$SYN_CLI marketplace list`
  - Fallback: check `~/.syntropic137/workflows/registries.json` if it exists
- `search <query>` → search available workflows
  - If SYN_CLI: `$SYN_CLI workflow search "<query>"`
  - Fallback: not available without CLI
- `install <plugin>` → install a workflow plugin from the marketplace
  - If SYN_CLI: `$SYN_CLI workflow install <plugin>`
  - Fallback: not available without CLI — suggest installing the CLI first
- `add <registry>` → register a new marketplace
  - If SYN_CLI: `$SYN_CLI marketplace add <registry>`
  - Fallback: not available without CLI

After installing a workflow plugin, suggest:
1. Running `/syn-workflows list` to verify the workflows were created
2. Running `/syn-triggers create --from-package <plugin>` to set up automatic triggers

For the default Syntropic137 marketplace, the registry is `syntropic137/syntropic137-marketplace`.
