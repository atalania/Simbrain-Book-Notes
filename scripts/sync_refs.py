#!/usr/bin/env python3
"""Keep the line-number references in notes/*.md in step with the upstream book.

How it works
------------
You write a reference in a note using a short tag, for example

    [[L:Transformers.tex:183]]          ->  "Line 183"   (capital L)
    [[l:AI_Alignment.tex:344-422]]      ->  "lines 344-422" (lower-case l)
    [[§:Transformers.tex:183]]          ->  "§1.1 In-Context Processing"
    [[s:Transformers.tex:183]]          ->  "§1.1" (section number only, for prose)
    [[L:Transformers.tex:183@1371c5d]]  ->  same, but "line 183 as of commit 1371c5d"

The first time this script sees a tag it gives it an id, stores a fingerprint
of the text around that line in .refs/refs.json, and rewrites the tag as

    <!--ref:r001-->[Line 183](https://github.com/.../blob/<sha>/Transformers.tex#L183)<!--/ref-->

On every later run it follows each line through the upstream history:

1. Diff mapping.  The file at the commit where the line was last confirmed is
   diffed against the latest commit.  If the line itself is unchanged, its new
   number follows exactly from the diff (lines inserted or deleted above it
   simply shift it).
2. Fuzzy matching.  If the line was edited, or the old commit is gone, the
   stored fingerprint (the line plus its neighbours) is compared with every
   line of the current file, preferring matches near the expected spot.
3. Other files.  If nothing in the same file matches well, every other .tex
   file is searched, so a passage moved into a new chapter file is still found.

The text between the markers is then regenerated, and STATUS.md lists every
reference together with anything that needs a human look.  Only the Python
standard library and git are needed.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
REGISTRY_PATH = ROOT / ".refs" / "refs.json"
STATUS_PATH = ROOT / "STATUS.md"
ACCEPT_PATH = ROOT / "accept.txt"

SHORT_RE = re.compile(
    r"\[\[(?P<kind>[Ll§s]):(?P<file>[^\]\s:@]+\.tex):(?P<start>\d+)(?:-(?P<end>\d+))?"
    r"(?:@(?P<commit>[0-9a-fA-F]{7,40}))?\]\]"
)
TRACKED_RE = re.compile(r"<!--ref:(?P<id>r\d+)-->(?P<body>.*?)<!--/ref-->", re.S)
HEADING_RE = re.compile(r"^\s*\\(?P<level>chapter|section|subsection|subsubsection)(?P<star>\*?)\s*(?:\[[^\]]*\])?\s*\{")

# Matching thresholds (0..1 similarity of the line plus its neighbours).
CONFIDENT = 0.90   # at or above: treated as the same passage, lightly edited
POSSIBLE = 0.60    # between POSSIBLE and CONFIDENT: linked, but flagged for review
OTHER_FILE = 0.85  # needed before accepting a match in a different .tex file


# --------------------------------------------------------------------------- git

class Upstream:
    def __init__(self, path: Path):
        self.path = path
        self._cache: dict[tuple[str, str], list[str] | None] = {}
        self._diff_cache: dict[tuple, list] = {}

    def git(self, *args: str, check: bool = True) -> str:
        res = subprocess.run(["git", "-C", str(self.path), *args],
                             capture_output=True, text=True)
        if check and res.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
        return res.stdout

    def resolve(self, rev: str) -> str | None:
        res = subprocess.run(["git", "-C", str(self.path), "rev-parse", "--verify", "--quiet",
                              f"{rev}^{{commit}}"], capture_output=True, text=True)
        return res.stdout.strip() or None

    def commit_date(self, sha: str) -> str:
        return self.git("log", "-1", "--format=%cd", "--date=format:%Y-%m-%d %H:%M %z", sha).strip()

    def lines(self, commit: str, path: str) -> list[str] | None:
        key = (commit, path)
        if key not in self._cache:
            res = subprocess.run(["git", "-C", str(self.path), "show", f"{commit}:{path}"],
                                 capture_output=True)
            if res.returncode != 0:
                self._cache[key] = None
            else:
                self._cache[key] = res.stdout.decode("utf-8", errors="replace").split("\n")
        return self._cache[key]

    def tex_files(self, commit: str) -> list[str]:
        key = ("tex_files", commit)
        if key not in self._diff_cache:
            out = self.git("ls-tree", "-r", "--name-only", commit)
            self._diff_cache[key] = [p for p in out.splitlines() if p.endswith(".tex")]
        return self._diff_cache[key]

    def line_index(self, commit: str) -> dict[str, list[tuple[str, int]]]:
        """Normalised line text -> every (file, line number) where it occurs, across all .tex files."""
        key = ("line_index", commit)
        if key not in self._diff_cache:
            index: dict[str, list[tuple[str, int]]] = {}
            for path in self.tex_files(commit):
                for n, line in enumerate(self.lines(commit, path) or [], start=1):
                    index.setdefault(norm(line), []).append((path, n))
            self._diff_cache[key] = index
        return self._diff_cache[key]

    def opcodes(self, old_commit: str, old_path: str, new_commit: str, new_path: str):
        key = (old_commit, old_path, new_commit, new_path)
        if key not in self._diff_cache:
            a = self.lines(old_commit, old_path) or []
            b = self.lines(new_commit, new_path) or []
            self._diff_cache[key] = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
        return self._diff_cache[key]

    def renamed_to(self, old_commit: str, new_commit: str, path: str) -> str | None:
        out = self.git("diff", "--name-status", "-M", old_commit, new_commit, check=False)
        for row in out.splitlines():
            parts = row.split("\t")
            if parts and parts[0].startswith("R") and len(parts) == 3 and parts[1] == path:
                return parts[2]
        return None


# ---------------------------------------------------------------- text helpers

def norm(s: str) -> str:
    return " ".join(s.split())


def fingerprint(lines: list[str], n: int) -> list[str]:
    """The line (1-based n) with one neighbour on each side, whitespace-normalised."""
    get = lambda k: norm(lines[k - 1]) if 1 <= k <= len(lines) else ""
    return [get(n - 1), get(n), get(n + 1)]


def similarity(fp: list[str], lines: list[str], n: int) -> float:
    cand = fingerprint(lines, n)
    centre = difflib.SequenceMatcher(None, fp[1], cand[1]).ratio() if (fp[1] or cand[1]) else 1.0
    window = difflib.SequenceMatcher(None, " ⏎ ".join(fp), " ⏎ ".join(cand)).ratio()
    return 0.6 * centre + 0.4 * window


def best_match(fp: list[str], lines: list[str], expected: int | None) -> tuple[int, float]:
    """Best-scoring line for a fingerprint.

    The centre line is screened first with difflib's cheap upper bounds
    (real_quick_ratio, then quick_ratio) on a matcher that keeps the target
    cached, so the full comparison only runs on plausible candidates.
    """
    best_n, best_score = 0, -1.0
    use_window = not fp[1]          # a blank target line: screen on the whole window instead
    target = " ⏎ ".join(fp) if use_window else fp[1]
    sm = difflib.SequenceMatcher(None)
    sm.set_seq2(target)
    floor = POSSIBLE * 0.6          # the centre can be this weak and still reach POSSIBLE overall
    target_window = " ⏎ ".join(fp)
    for n in range(1, len(lines) + 1):
        cand = " ⏎ ".join(fingerprint(lines, n)) if use_window else norm(lines[n - 1])
        sm.set_seq1(cand)
        if sm.real_quick_ratio() < floor or sm.quick_ratio() < floor:
            continue
        if use_window:
            score = similarity(fp, lines, n)
        else:
            centre = sm.ratio()
            # Even a perfect window could not lift this candidate above the current best.
            if 0.6 * centre + 0.4 < max(best_score, POSSIBLE):
                continue
            window = difflib.SequenceMatcher(None, target_window, " ⏎ ".join(fingerprint(lines, n))).ratio()
            score = 0.6 * centre + 0.4 * window
        if expected is not None:  # tiny tie-breaker toward the expected position
            score -= 1e-6 * abs(n - expected)
        if score > best_score:
            best_n, best_score = n, score
    return best_n, best_score


def latex_title(text: str) -> str:
    """Extract and tidy the {...} argument that starts at the first '{'."""
    depth, out = 0, []
    for ch in text[text.index("{"):]:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
    t = "".join(out)
    t = t.replace("``", '"').replace("''", '"').replace("\\ ", " ").replace("~", " ")
    for _ in range(3):
        t = re.sub(r"\\[a-zA-Z]+\*?\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\[a-zA-Z]+\*?", "", t).replace("{", "").replace("}", "")
    return norm(t)


def section_at(lines: list[str], n: int, chapter_number: str) -> tuple[str, int]:
    """Return ('§1.6.2 Title', heading_line) for the innermost heading at or above line n."""
    counters = [0, 0, 0]
    current = ("§ chapter introduction", 1)
    levels = {"section": 0, "subsection": 1, "subsubsection": 2}
    for k in range(1, min(n, len(lines)) + 1):
        line = lines[k - 1]
        if line.lstrip().startswith("%"):
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        title = latex_title(line[m.start():])
        level = m.group("level")
        if level == "chapter":
            counters = [0, 0, 0]
            current = ("§ chapter introduction", k)
            continue
        if m.group("star"):
            current = (f"§ {title}", k)
            continue
        d = levels[level]
        counters[d] += 1
        for j in range(d + 1, 3):
            counters[j] = 0
        number = ".".join([chapter_number] + [str(c) for c in counters[: d + 1]])
        current = (f"§{number} {title}", k)
    return current


# ------------------------------------------------------------------- tracking

def locate(up: Upstream, file: str, n: int, fp: list[str], old_commit: str, head: str):
    """Find where line n of `file` at old_commit is at head.

    Returns (file, line, status, score) with status one of
    exact | edited | review | moved-file | lost.
    """
    new_file = file
    head_lines = up.lines(head, file)
    if head_lines is None:
        renamed = up.renamed_to(old_commit, head, file) if up.resolve(old_commit) else None
        if renamed:
            new_file, head_lines = renamed, up.lines(head, renamed)

    expected = None       # where the diff says the line should be
    rewritten_at = None   # set when the diff shows the line was replaced in place
    if head_lines is not None and up.lines(old_commit, file) is not None:
        for tag, i1, i2, j1, j2 in up.opcodes(old_commit, file, head, new_file):
            if i1 <= n - 1 < i2:
                if tag == "equal":
                    return new_file, j1 + (n - 1 - i1) + 1, "exact", 1.0
                if tag == "replace":
                    # Same spot, new wording: scale the offset into the new block.
                    offset = round((n - 1 - i1) * (j2 - j1) / (i2 - i1))
                    rewritten_at = j1 + min(offset, j2 - j1 - 1) + 1
                expected = rewritten_at or j1 + 1
                break
        else:  # past the end of the old file
            expected = len(head_lines)

    if head_lines is not None:
        line, score = best_match(fp, head_lines, expected if expected else n)
        if score >= CONFIDENT:
            return new_file, line, "edited", score
        # Before settling for a weak match, see whether the passage moved files.
        other = search_other_files(up, fp, head, exclude=new_file)
        if other and other[2] > max(score, POSSIBLE):
            return other[0], other[1], "moved-file", other[2]
        if score >= POSSIBLE:
            return new_file, line, "review", score
        if rewritten_at:
            # The text was rewritten where it stood: keep the position, ask for a check.
            return new_file, rewritten_at, "review", similarity(fp, head_lines, rewritten_at)
        return file, n, "lost", 0.0

    other = search_other_files(up, fp, head, exclude=new_file)
    if other:
        return other[0], other[1], "moved-file", other[2]
    return file, n, "lost", 0.0


def search_other_files(up: Upstream, fp: list[str], head: str, exclude: str):
    """Look for the passage in every other .tex file (for text moved between chapters).

    Exact copies of the line are found through an index first. The slower fuzzy
    search only runs for distinctive lines (at least 20 characters), since short
    lines such as "\\end{quote}" occur everywhere.
    """
    if not fp[1]:
        return None
    best = None
    exact = up.line_index(head).get(fp[1], [])
    for path, n in exact:
        if path == exclude:
            continue
        score = similarity(fp, up.lines(head, path) or [], n)
        if score >= OTHER_FILE and (best is None or score > best[2]):
            best = (path, n, score)
    if best or len(fp[1]) < 20:
        return best
    for path in up.tex_files(head):
        if path == exclude:
            continue
        line, score = best_match(fp, up.lines(head, path) or [], None)
        if score >= OTHER_FILE and (best is None or score > best[2]):
            best = (path, line, score)
    return best


# ------------------------------------------------------------------ rendering

def permalink(cfg: dict, sha: str, file: str, start: int, end: int | None) -> str:
    anchor = f"#L{start}" + (f"-L{end}" if end and end != start else "")
    return f"https://github.com/{cfg['upstream_repo']}/blob/{sha}/{file}{anchor}"


def render(ref: dict, cfg: dict, up: Upstream, head: str) -> str:
    kind, file, start, end = ref["kind"], ref["file"], ref["start"], ref.get("end")
    status = ref["status"]
    flag = {"review": " ⚠️", "moved-file": " ↪️"}.get(status, "")
    moved_note = f" of {file}" if file != ref["orig"]["file"] else ""

    if status in ("lost", "retired"):
        word = "Line" if kind in "L§" else "line"
        span = f"{ref['orig']['start']}" + (f"-{ref['orig']['end']}" if ref["orig"].get("end") else "")
        plural = "s" if ref["orig"].get("end") else ""
        if status == "retired":
            return f"{word}{plural} {span} (since removed from the book)"
        return f"{word}{plural} {span} ❌ (not found upstream — see STATUS.md)"

    if kind in ("§", "s"):
        lines = up.lines(head, file) or []
        chap = str(cfg.get("chapter_numbers", {}).get(file, cfg.get("default_chapter_number", "1")))
        label, heading_line = section_at(lines, start, chap)
        if kind == "s":  # short form: just "§1.6.3" (an unnumbered heading keeps its title)
            m = re.match(r"§(\d[\d.]*) ", label)
            label = f"§{m.group(1)}" if m else label
        if moved_note:
            label += f" ({file})"
        return f"[{label}]({permalink(cfg, head, file, heading_line, None)}){flag}"

    word = "Line" if kind == "L" else "line"
    if end and end != start:
        text = f"{word}s {start}-{end}{moved_note}"
    else:
        text = f"{word} {start}{moved_note}"
    return f"[{text}]({permalink(cfg, head, file, start, end)}){flag}"


# ------------------------------------------------------------------ main flow

def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


ACCEPT_HEADER = """\
# List ref ids here (for example: r017 r018), one or more per line, to accept them
# after you have checked them in STATUS.md:
#   ⚠️ or ↪️  -> the flag is cleared and the link stays where it is
#   ❌         -> the reference is retired and shown as "since removed from the book"
# The sync empties this file again once it has applied the list.
"""


def read_accept_list() -> list[str]:
    if not ACCEPT_PATH.exists():
        return []
    ids = []
    for line in ACCEPT_PATH.read_text(encoding="utf-8").splitlines():
        ids += re.findall(r"\br\d+\b", line.split("#", 1)[0])
    return ids


def note_files(cfg: dict) -> list[Path]:
    files: list[Path] = []
    for pattern in cfg.get("notes", ["notes/**/*.md"]):
        files.extend(sorted(ROOT.glob(pattern)))
    return [f for f in files if f.is_file()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--upstream", required=True, type=Path, help="path to a clone of the book repo")
    ap.add_argument("--rev", default=None, help="upstream revision to sync to (default: config branch)")
    ap.add_argument("--summary-file", type=Path, help="write a one-line summary here (for commit messages)")
    ap.add_argument("--attention-file", type=Path,
                    help="write a GitHub issue body listing flagged references here (empty file if none)")
    args = ap.parse_args()

    cfg = load_json(CONFIG_PATH, {})
    up = Upstream(args.upstream)
    head = up.resolve(args.rev or f"origin/{cfg.get('upstream_branch', 'main')}") or up.resolve("HEAD")
    if not head:
        sys.exit("Could not resolve the upstream revision.")

    registry = load_json(REGISTRY_PATH, {"refs": {}})
    refs: dict = registry["refs"]
    next_id = max([int(k[1:]) for k in refs] or [0]) + 1
    problems: list[str] = []
    used: dict[str, str] = {}

    # Pass 1: register new short tags.
    for path in note_files(cfg):
        text = path.read_text(encoding="utf-8")

        def register(m: re.Match) -> str:
            nonlocal next_id
            commit = up.resolve(m.group("commit")) if m.group("commit") else head
            file, start = m.group("file"), int(m.group("start"))
            end = int(m.group("end")) if m.group("end") else None
            lines = up.lines(commit, file) if commit else None
            where = f"{path.relative_to(ROOT)}: {m.group(0)}"
            if not commit:
                problems.append(f"{where} — unknown commit {m.group('commit')}")
                return m.group(0)
            if lines is None:
                problems.append(f"{where} — {file} does not exist at {commit[:7]}")
                return m.group(0)
            if not (1 <= start <= len(lines)) or (end and not start <= end <= len(lines)):
                problems.append(f"{where} — line out of range ({file} has {len(lines)} lines)")
                return m.group(0)
            rid = f"r{next_id:03d}"
            next_id += 1
            refs[rid] = {
                "kind": m.group("kind"), "file": file, "start": start, "end": end,
                "commit": commit, "status": "exact",
                "fp_start": fingerprint(lines, start),
                "fp_end": fingerprint(lines, end) if end else None,
                "orig": {"file": file, "start": start, "end": end, "commit": commit,
                         "text": norm(lines[start - 1])},
            }
            return f"<!--ref:{rid}-->{m.group(0)}<!--/ref-->"

        new_text = SHORT_RE.sub(register, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    # Pass 2: move every referenced entry forward to head.
    moved = 0
    for path in note_files(cfg):
        for m in TRACKED_RE.finditer(path.read_text(encoding="utf-8")):
            used.setdefault(m.group("id"), str(path.relative_to(ROOT)))

    # Flags you have checked: ids listed in accept.txt are cleared (or retired, if not found).
    accepted = read_accept_list()
    for rid in accepted:
        ref = refs.get(rid)
        if ref is None:
            problems.append(f"accept.txt: unknown ref {rid}")
        elif ref["status"] == "lost":
            ref["status"] = "retired"
        elif ref["status"] in ("review", "moved-file"):
            ref["status"] = "exact"

    for rid in sorted(used):
        ref = refs.get(rid)
        if ref is None:
            problems.append(f"{used[rid]}: marker {rid} has no entry in .refs/refs.json")
            continue
        if ref["status"] == "retired" or (ref["commit"] == head and ref["status"] != "lost"):
            continue
        previous = ref["status"]
        old = (ref["file"], ref["start"], ref.get("end"))
        f1, s1, st1, sc1 = locate(up, ref["file"], ref["start"], ref["fp_start"], ref["commit"], head)
        status, score = st1, sc1
        e1 = None
        if ref.get("end"):
            f2, e1, st2, sc2 = locate(up, ref["file"], ref["end"], ref["fp_end"], ref["commit"], head)
            rank = ["exact", "edited", "moved-file", "review", "lost"]
            if st1 == "lost" and st2 != "lost":       # keep what we can
                f1, s1, status, score = f2, e1, st2, sc2
            elif f2 != f1 or e1 < s1:
                e1 = s1
                status = "review" if status != "lost" else status
            else:
                status = max(st1, st2, key=rank.index)
                score = min(sc1, sc2)
        ref["score"] = round(score, 3)
        if previous in ("review", "moved-file") and status in ("exact", "edited"):
            status = previous  # a flag stays until someone accepts it in accept.txt
        if status == "lost":
            ref["status"] = "lost"
            continue
        lines = up.lines(head, f1) or []
        ref.update(file=f1, start=s1, end=e1, commit=head, status=status,
                   fp_start=fingerprint(lines, s1),
                   fp_end=fingerprint(lines, e1) if e1 else None)
        if (f1, s1, e1) != old:
            moved += 1

    # Pass 3: re-render every marker.
    for path in note_files(cfg):
        text = path.read_text(encoding="utf-8")

        def rerender(m: re.Match) -> str:
            ref = refs.get(m.group("id"))
            if ref is None:
                return m.group(0)
            return f"<!--ref:{m.group('id')}-->{render(ref, cfg, up, head)}<!--/ref-->"

        new_text = TRACKED_RE.sub(rerender, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")

    if accepted:
        ACCEPT_PATH.write_text(ACCEPT_HEADER, encoding="utf-8")
    registry["upstream_commit"] = head
    REGISTRY_PATH.parent.mkdir(exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_status(cfg, up, head, refs, used, problems)
    if args.attention_file:
        args.attention_file.write_text(issue_body(cfg, head, refs, used, problems), encoding="utf-8")

    statuses = [refs[r]["status"] for r in used if r in refs]
    review = sum(s in ("review", "moved-file") for s in statuses)
    lost = statuses.count("lost")
    summary = (f"sync to upstream {head[:7]}: {len(used)} refs, {moved} moved, "
               f"{review} to review, {lost} not found")
    print(summary)
    for p in problems:
        print("  problem:", p)
    if args.summary_file:
        args.summary_file.write_text(summary + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(f"### {summary}\n\n" + "".join(f"- {p}\n" for p in problems))
    return 0


def issue_body(cfg, head: str, refs: dict, used: dict, problems: list[str]) -> str:
    """Body for the 'references need attention' issue; empty when nothing is flagged.

    Text quoted from the book goes inside `code` spans, where GitHub does not turn
    @names into mentions or #numbers into issue links, so the issue can never
    notify anyone else.
    """
    flagged = [r for r in sorted(used) if r in refs and refs[r]["status"] in ("review", "moved-file", "lost")]
    if not flagged and not problems:
        return ""
    labels = {"review": "⚠️ check", "moved-file": "↪️ moved file", "lost": "❌ not found"}
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    status_link = f"https://github.com/{repo}/blob/main/STATUS.md" if repo else "STATUS.md"

    def code(s: str) -> str:
        s = s.replace("`", "'").replace("|", "\\|")
        return f"`{s[:87] + '…' if len(s) > 90 else s}`" if s else ""

    out = [f"<!-- ids: {' '.join(flagged)} -->",
           f"After the book changed (now at `{head[:7]}`), these references in the notes need a look. "
           f"Open each link in [STATUS.md]({status_link}) and check it.", "",
           "- **The link is right** (or, for ❌, the passage really is gone): add the id to `accept.txt`.",
           "- **The link is wrong:** replace its `<!--ref:…-->…<!--/ref-->` in the note with a fresh `[[L:File.tex:line]]` tag.",
           "", "This issue updates itself and closes once nothing is flagged.", ""]
    if flagged:
        out += ["| Ref | Note | Originally | Status | Text it was anchored to |", "|---|---|---|---|---|"]
        for rid in flagged:
            ref = refs[rid]
            o = ref["orig"]
            span = f"{o['start']}" + (f"-{o['end']}" if o.get("end") else "")
            out.append(f"| `{rid}` | `{used[rid]}` | `{o['file']}:{span}` | {labels[ref['status']]} | "
                       f"{code(o.get('text', ref['fp_start'][1]))} |")
    if problems:
        out += ["", "**Tags that could not be registered:**", *[f"- {code(p)}" for p in problems]]
    return "\n".join(out) + "\n"


def write_status(cfg, up: Upstream, head: str, refs: dict, used: dict, problems: list[str]) -> None:
    def cell(s: str) -> str:
        s = s.replace("|", "\\|").replace("<", "&lt;")
        return s if len(s) <= 90 else s[:87] + "…"

    def where(ref):
        span = f"{ref['start']}" + (f"-{ref['end']}" if ref.get("end") else "")
        url = permalink(cfg, head, ref["file"], ref["start"], ref.get("end"))
        return f"[{ref['file']}:{span}]({url})"

    def orig(ref):
        o = ref["orig"]
        return f"{o['file']}:{o['start']}" + (f"-{o['end']}" if o.get("end") else "") + f" @{o['commit'][:7]}"

    labels = {"exact": "✅ exact", "edited": "✏️ text edited", "review": "⚠️ check",
              "moved-file": "↪️ moved file", "lost": "❌ not found", "retired": "🗄️ retired"}
    rows_attention, rows_all = [], {}
    for rid in sorted(used):
        ref = refs.get(rid)
        if not ref:
            continue
        current = ""
        gone = ref["status"] in ("lost", "retired")
        if not gone:
            lines = up.lines(head, ref["file"]) or []
            if 1 <= ref["start"] <= len(lines):
                current = norm(lines[ref["start"] - 1])
        row = (f"| `{rid}` | {'—' if gone else where(ref)} | {orig(ref)} | "
               f"{labels[ref['status']]} | {cell(current)} |")
        rows_all.setdefault(used[rid], []).append(row)
        if ref["status"] in ("review", "moved-file", "lost"):
            fp = cell(ref["orig"].get("text", ref["fp_start"][1]))
            rows_attention.append(f"| `{rid}` | {used[rid]} | {orig(ref)} | {labels[ref['status']]} | {fp} |")

    head_row = "| Ref | Now points to | Originally | Status | Text on that line now |\n|---|---|---|---|---|"
    out = [
        "# Reference status",
        "",
        "_Generated by `scripts/sync_refs.py`; do not edit by hand._",
        "",
        f"Synced to upstream commit [`{head[:7]}`](https://github.com/{cfg['upstream_repo']}/commit/{head}) "
        f"({up.commit_date(head)}).",
        "",
        "Legend: ✅ the line is unchanged and its number was carried through the diff · "
        "✏️ the line was lightly edited upstream and matched by text · "
        "⚠️ a weak match: please check it and fix the tag if needed · "
        "↪️ the passage was found in a different .tex file · "
        "❌ the text could not be found (it may have been deleted, which often means the suggestion was addressed).",
        "",
        "## Needs attention",
        "",
        "Open each link and check it. When a reference is fine (or, for ❌, when the passage really is gone), "
        "add its id to [`accept.txt`](accept.txt) and the flag is cleared on the next sync. "
        "If a link points to the wrong place, replace its `<!--ref:…-->…<!--/ref-->` in the note with a fresh "
        "`[[L:File.tex:line]]` tag.",
        "",
    ]
    if rows_attention:
        out += ["| Ref | Note | Originally | Status | Text it was anchored to |", "|---|---|---|---|---|",
                *rows_attention, ""]
    else:
        out += ["Nothing. Every reference was located confidently.", ""]
    if problems:
        out += ["## Tags that could not be registered", "", *[f"- {p}" for p in problems], ""]
    for note, rows in rows_all.items():
        out += [f"## {note}", "", head_row, *rows, ""]
    STATUS_PATH.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
