---
name: session-discovery
description: Find and review every agent session of a Syntropic137 workflow run, including delegates and native transcripts; read coverage and gaps correctly, follow lineage, fetch transcripts, and run a learning-loop review of what the agents did. Use for "all sessions of exec-...", "what did the delegates do", "which sub-agent failed", "pull the transcripts of this run", "review this run"
---

# Session Discovery: Syntropic137

A workflow run is rarely one agent. A phase agent can delegate to `claude -p` or `codex exec` inside its workspace, delegates can spawn children, and resumes continue earlier work. `syn sessions list` shows only platform sessions. **The session inventory shows every session of a run, how they relate, which transcripts were captured, and whether the list is known to be complete.** Never conclude "the run had N agents" or "nothing failed" from a list whose coverage is not `reconciled`.

Public guide: https://docs.syntropic137.com/docs/guide/session-discovery

## When to Use This Skill

Use it when asked to list or count the sessions of an execution, find what a delegate or sub-agent did, find failed or missing delegates, fetch transcripts of a run, or review a run to improve the workflow (a learning loop).

Not for cost or token questions on one session: use observability. Not for controlling a running execution: use execution-control.

## Step 1: Summary

```bash
syn execution show <execution-id>
```

The output ends with `Session inventory:` (counts), `Coverage:` and `Details:` (the exact follow-up command). Print these server-written lines verbatim; do not recompute them.

## Step 2: Every session, from one pinned revision

```bash
syn execution sessions <execution-id> --all --json > inventory.json
```

Always pass `--all`. Without it you get only the first page of one section, and the CLI says the listing is partial. JSON fields to read first: `summary.coverage_state`, `summary.coverage_display`, `summary.counts_display`, `complete`, `coverage_complete`, `traversal_complete`, `pending_sections`, `gaps`.

Human view: `syn execution sessions <execution-id> --all` groups sessions by phase and attempt, then unlinked sessions, then gaps.

For automation that must not act on a partial list, add `--require-complete`: the command prints what it read, then exits nonzero unless coverage is `reconciled`, the revision is current, and every section was read unfiltered.

## Reading the Result

**Namespaces.** `platform` (a session the platform created and bills; works with `syn sessions show`), `invocation` (a registered agent process launch inside a workspace, such as a delegate), `transcript:<harness>` (the harness's own native session ID). A native ID is never a platform session ID: never pass one to `syn sessions show`. A `binding` says a platform session or invocation represents a native transcript; count them as one piece of work.

**Coverage** (`summary.coverage_state`):

| State | What you may conclude |
|---|---|
| `reconciled` | Complete when `summary.complete` is true |
| `open` | NOT complete: the run is running or still settling (up to the settlement grace, default 30 minutes after it ends). Say so and re-check later |
| `missing` | Settled with known sessions or captures unaccounted for: the gaps name them |
| `conflicting` | Evidence disagrees: report the conflicting gaps, do not pick a side |
| `unsupported` | Completeness cannot be proven (legacy run, unsupported harness) |
| `unknown` | No contract or no published revision yet |

`complete` is true only for `reconciled` coverage on a current revision. Treat everything else as a partial view and say which state it is in.

**Gaps** (`gaps[]`, each with `reason` and affected `node_keys`). The ones that answer "which delegate failed":

- `invocation_failed`, `invocation_cancelled`, other `invocation_<outcome>`: the process ended abnormally.
- `invocation_launch_failed` and `invocation_launch_failed_<cause>` (`process_start_failed`, `codex_sandbox_unavailable`, `native_tool_failed`, `native_tool_interrupted`, `capture_hook_failed`, `hook_watchdog`, `capture_hook_unreachable`): it never started.
- `invocation_transport_failed_before_announce`: failed before announcing; not known to have run.
- `invocation_running`, `invocation_pending`: no outcome yet (provisional while `open`).
- `*_at_seal` (`invocation_unsettled_at_seal`, `capture_unsettled_at_seal`, `child_context_unresolved_at_seal`, `parentage_unresolved_at_seal`): still unsettled when the deadline passed.
- `expected_body_unavailable`: an expected session has no present transcript.
- `conflicting_*`, `lineage_cycle`, `unresolved_parentage`, `unverified_invocation_context`: identity, parentage or attribution evidence disagrees or is unverified.
- `no_host_registration`: the run was not instrumented, coverage `unsupported`.

The vocabulary is open: report an unfamiliar reason as a gap, never ignore it. A gap with no `node_keys` applies to the whole run.

Map gap node keys to sessions with the node pages (`item_keys[i].node_key` names `items[i]`):

```bash
jq -r '
  ([.pages[] | select(.kind == "node") | . as $p
    | range(0; $p.items | length)
    | {key: $p.item_keys[.].node_key, value: $p.items[.].ref}] | from_entries) as $nodes
  | .gaps[]? | .reason as $r
  | if (.node_keys | length) == 0 then "\($r)\t(run-level)"
    else .node_keys[] | "\($r)\t\($nodes[.].kind // "?"):\($nodes[.].harness // "-")\t\($nodes[.].local_id // .)"
    end' inventory.json
```

## Lineage

Edges link parent to child with `relation` `spawn` (started a delegate), `resume` (continues a conversation) or `fork` (branched), plus a confidence (`registered`, `corroborated`, `candidate`, `conflicting`):

```bash
jq -r '.pages[] | select(.kind == "edge") | .items[]
  | "\(.parent.kind):\(.parent.local_id) -[\(.relation)]-> \(.child.kind):\(.child.local_id) (\(.confidence))"' inventory.json
```

## Transcripts

A capture receipt with `destination` `local` and `availability` `present` carries `archived_byte_hash`, the read key:

```bash
syn execution transcript <execution-id> <harness> <native-id> <archived-bytes-sha256> --json
```

`--json` returns the normalized `conversation` (read this) and base64 bytes; `--raw` writes the exact bytes. A body that is `not_captured`, `missing`, `expired`, `deleted` or `too_large` exits nonzero with that status, and a revoked body is refused: report it as unavailable, never as "the agent did nothing". Receipts are history; the CLI's `current=` value (body overrides `expired`, `deleted`, `withheld`) is the body's state now. Remote receipts carry a replica content hash (`sha256:...`) that the local transcript route cannot read.

Pull every local transcript of a run:

```bash
mkdir -p transcripts
jq -r '.pages[] | select(.kind == "capture") | .items[]
  | select((.destination // "local") == "local" and .availability == "present")
  | [.node.harness, .node.local_id, .archived_byte_hash] | @tsv' inventory.json | sort -u |
while IFS=$'\t' read -r harness native sha; do
  syn execution transcript "$EXEC" "$harness" "$native" "$sha" --json \
    > "transcripts/${harness}-${native//\//_}-${sha:0:12}.json" || echo "unavailable: $harness $native"
done
```

## Without the CLI

All under `$SYN_API_URL/api/v1`, same credential as the rest of the API. Reads never trigger capture or reconstruction.

- `GET /executions/{id}/session-inventory`: `summary`, `snapshot.snapshot_id`, `reconstruction_status`.
- `GET /executions/{id}/session-inventory/{snapshot_id}/{kind}?limit=500`: kinds `node`, `membership`, `edge`, `capture`, `gap`, `binding`, `retraction`. Repeat with `cursor=<next_cursor>` until it is null. On `410 cursor_expired` restart from the summary.
- `GET /executions/{id}/session-inventory/{snapshot_id}/nodes/{node_key}`: resolve a key from another page.
- `GET /executions/{id}/session-transcripts/{archive_sha256}?harness=<h>&native_id=<id>`: one transcript.

Read-only by default. Do not call the reconcile, backfill, revocation or deletion routes unless the user asks: deletion erases transcript bytes for every run that shares them and cannot be undone.

## Central Replica (SeshMagic)

When `summary.remote_replication` is `enabled`, the inventory is also replicated to a SeshMagic store. Query it with its own read token, by the `source_instance_id` and `execution_id` from the inventory response: `GET <store>/v1/workflow-runs/{source_instance_id}/{execution_id}/sessions`, or the SeshMagic MCP tool `workflow_run_sessions`. The replica can trail the local inventory.

## Learning-Loop Review

1. `syn execution sessions <id> --all --json --require-complete > inventory.json`. If it fails on `open`, the run is settling: tell the user and offer to re-check later. On `missing`, `conflicting` or `unsupported`, continue but label the review partial and list the gaps.
2. Build the delegation tree from edges and memberships (phase and attempt per session).
3. List failed, never-launched and missing delegates from the gaps, with their parent.
4. Pull transcripts; for each session note what it was asked, what it did, how it ended.
5. Report: per phase, which agents ran and how they ended; failures with cause; duplicated or wasted work; prompt or workflow changes that would prevent each problem. Quote the coverage line verbatim at the top so the reader knows how complete the review is.

## Integration

Pairs with observability (tool timelines and cost of one platform session: `syn observe tools <session-id>`), troubleshooting-workflow-failures (root cause of a failed phase), and workflow-management (turn review findings into YAML and prompt changes).
