"""Validate every ```yaml example in this plugin's docs against the real loader.

The skills teach workflow authors what YAML to write. When the examples drift
from the validator, authors lose validate-fix cycles on keys the docs told
them to use. This script runs each example through the platform's own
`WorkflowDefinition.from_file`, the loader `syn workflow install` relies on,
so a stale example fails here instead of there.

What is checked, per block:
  - the schema (every model is `extra="forbid"`, so unknown keys fail);
  - `prompt_file` resolution, relative to the doc's own directory, so a
    reference to a missing file fails;
  - conversion of every phase to the domain `PhaseDefinition`.
What is NOT checked: anything the API does after parsing (plugin/skill
resolution, install provenance) and anything decided at execution time.

A block is either a complete workflow (has `id` and `phases`) or a fragment.
Fragments are wrapped in a minimal workflow: a missing `id`/`name` is filled
in, and a missing `phases` gets one trivial phase. Anything else in the block
is validated as written, including every phase it declares.

THE SCHEMA REVISION IS WHATEVER SYNTROPIC137 CHECKOUT YOU RUN IT WITH, so the
script prints that checkout's path and commit, and refuses to run unless the
commit equals that checkout's `origin/main` (fetch first). Validate against
a detached origin/main worktree, never a feature branch:

    git -C <syntropic137> fetch origin
    git -C <syntropic137> worktree add --detach <wt> origin/main
    git -C <wt> submodule update --init lib/agentic-workspace lib/event-sourcing-platform
    uv sync --project <wt>
    uv run --project <wt> python scripts/validate_yaml_examples.py

Pass `--allow-any-ref` to validate against a different revision on purpose.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```ya?ml\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
TRIVIAL_PHASE = {"id": "example", "name": "Example", "order": 1, "prompt_template": "x"}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _schema_revision(module_file: str) -> tuple[Path, str, str]:
    """The syntropic137 checkout the schema was imported from, its HEAD, and its origin/main."""
    repo = Path(_git(Path(module_file).parent, "rev-parse", "--show-toplevel"))
    return repo, _git(repo, "rev-parse", "HEAD"), _git(repo, "rev-parse", "origin/main")


def _wrap(data: object) -> object:
    if not isinstance(data, dict):
        return data
    wrapped: dict[str, object] = {"id": "doc-example", "name": "Doc example"}
    wrapped.update(data)
    wrapped.setdefault("phases", [TRIVIAL_PHASE])
    return wrapped


def _validate_block(workflow_definition: type, block: str, doc_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.yaml"
        path.write_text(yaml.safe_dump(_wrap(yaml.safe_load(block))), encoding="utf-8")
        definition = workflow_definition.from_file(path, base_dir=doc_dir)
    for phase in definition.phases:
        phase.to_domain()


def main() -> int:
    from syn_domain.contexts.orchestration._shared import workflow_definition as wd

    try:
        repo, head, origin_main = _schema_revision(wd.__file__)
    except subprocess.CalledProcessError as exc:
        print(
            f"refusing: cannot read the git revision of the schema at {wd.__file__}: "
            f"{exc.stderr.strip()}",
            file=sys.stderr,
        )
        return 2
    print(f"schema: {repo} @ {head}")
    if head != origin_main and "--allow-any-ref" not in sys.argv:
        print(
            f"refusing: {head[:12]} is not origin/main ({origin_main[:12]}). "
            "Run against an origin/main worktree, or pass --allow-any-ref.",
            file=sys.stderr,
        )
        return 2

    docs = sorted(p for p in PLUGIN_ROOT.rglob("*.md") if ".git" not in p.parts)
    checked = 0
    failures: list[str] = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for match in FENCE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            where = f"{doc.relative_to(PLUGIN_ROOT)}:{line}"
            checked += 1
            try:
                _validate_block(wd.WorkflowDefinition, match.group(1), doc.parent)
            except Exception as exc:  # noqa: BLE001 (report every failure, do not stop)
                failures.append(f"{where}\n{type(exc).__name__}: {exc}")
    for failure in failures:
        print(f"FAIL {failure}\n", file=sys.stderr)
    print(f"{checked - len(failures)}/{checked} YAML examples valid")
    return 1 if failures or checked == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
