#!/usr/bin/env python3
"""Decide whether the sync workflow needs to do any work.

Run by .github/workflows/sync-refs.yml before anything touches the book's
repository. It answers "skip" when:

- the run was started by the schedule (or the optional book-updated ping),
- and either the book has no new commits since the last sync,
- or none of the new commits changed a .tex file that the notes reference.

Runs you start yourself (pushing to the notes, or "Run workflow") always sync,
so new [[L:...]] tags are registered straight away.

The book's changed files come from GitHub's compare API, one API call that
does not count as a clone or a visit in the book's traffic statistics. If that
call fails, or the book's history was rewritten, it plays safe and syncs.

Usage:
  decide_sync.py --event EVENT --repo OWNER/NAME --sha LATEST_SHA [--compare-json FILE]

--compare-json reads a saved compare response instead of calling `gh api`
(for testing). Writes skip=true|false and reason=... to $GITHUB_OUTPUT when set,
and always prints the reason.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / ".refs" / "refs.json"
ALWAYS_RUN = {"push", "workflow_dispatch"}


def referenced_files(registry: dict) -> set[str]:
    files = set()
    for ref in registry.get("refs", {}).values():
        files.add(ref["file"])
        files.add(ref.get("orig", {}).get("file", ref["file"]))
    return files


def compare(repo: str, base: str, head: str, saved: Path | None) -> dict | None:
    if saved:
        return json.loads(saved.read_text(encoding="utf-8"))
    res = subprocess.run(["gh", "api", f"repos/{repo}/compare/{base}...{head}"],
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Compare API call failed ({res.stderr.strip()[:200]}); syncing to be safe.")
        return None
    return json.loads(res.stdout)


def decide(event: str, repo: str, sha: str, saved: Path | None) -> tuple[bool, str]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}
    known = registry.get("upstream_commit", "")

    if event in ALWAYS_RUN:
        return False, f"started by {event}: syncing"
    if not known:
        return False, "no previous sync recorded: syncing"
    if sha == known:
        return True, f"the book is still at {sha[:7]}: nothing to do"

    data = compare(repo, known, sha, saved)
    if data is None:
        return False, "could not list the book's changes: syncing"
    if data.get("status") not in ("ahead", "identical"):
        return False, f"the book's history changed (compare status: {data.get('status')}): syncing"

    changed = set()
    for f in data.get("files", []):
        changed.add(f.get("filename", ""))
        if f.get("previous_filename"):
            changed.add(f["previous_filename"])
    if len(data.get("files", [])) >= 300:
        return False, "too many changed files to list: syncing"

    relevant = sorted(changed & referenced_files(registry))
    n = data.get("total_commits", "?")
    if relevant:
        return False, f"{n} new book commit(s) changed {', '.join(relevant)}: syncing"
    return True, (f"{n} new book commit(s) since {known[:7]}, none touching the referenced "
                  f"chapters: nothing to do")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--event", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--compare-json", type=Path)
    args = ap.parse_args()

    skip, reason = decide(args.event, args.repo, args.sha, args.compare_json)
    print(reason)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"skip={'true' if skip else 'false'}\nreason={reason}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
