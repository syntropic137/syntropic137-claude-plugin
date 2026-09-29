"""Validate every ```yaml example in this plugin's docs against the real schema.

The skills teach workflow authors what YAML to write. When the examples drift
from the validator, authors lose validate-fix cycles on keys the docs told
them to use. This script runs each example through the platform's own
`WorkflowDefinition` model, so a stale example fails here instead of there.

A block is either a complete workflow (has `id` and `phases`) or a fragment.
Fragments are wrapped in a minimal workflow: a missing `id`/`name` is filled
in, and a missing `phases` gets one trivial phase. Anything else in the block
is validated as written, including every phase it declares.

Requires a synced Syntropic137 checkout; run it with that repo's environment:

    uv run --project <syntropic137> python scripts/validate_yaml_examples.py

Validate against the ref you ship against (normally origin/main), not a stale
feature branch: the schema changes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```ya?ml\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
TRIVIAL_PHASE = {"id": "example", "name": "Example", "order": 1, "prompt_template": "x"}


def _wrap(data: object) -> object:
    if not isinstance(data, dict):
        return data
    wrapped: dict[str, object] = {"id": "doc-example", "name": "Doc example"}
    wrapped.update(data)
    wrapped.setdefault("phases", [TRIVIAL_PHASE])
    return wrapped


def main() -> int:
    from syn_domain.contexts.orchestration._shared.workflow_definition import (
        WorkflowDefinition,
    )

    docs = sorted(
        p for p in PLUGIN_ROOT.rglob("*.md") if ".git" not in p.parts
    )
    checked = 0
    failures: list[str] = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for match in FENCE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            where = f"{doc.relative_to(PLUGIN_ROOT)}:{line}"
            checked += 1
            try:
                WorkflowDefinition.model_validate(_wrap(yaml.safe_load(match.group(1))))
            except Exception as exc:  # noqa: BLE001 (report every failure, do not stop)
                failures.append(f"{where}\n{exc}")
    for failure in failures:
        print(f"FAIL {failure}\n", file=sys.stderr)
    print(f"{checked - len(failures)}/{checked} YAML examples valid")
    return 1 if failures or checked == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
