#!/usr/bin/env python3
"""REQ-CB-1 gate — the theme must never forward a consuming site's line-number config.

Builds ``exampleSite`` twice. The second build forces the reference site's own hostile
configuration through environment variables::

    HUGO_MARKUP_HIGHLIGHT_LINENOS=true
    HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true

The two output trees must be **byte-identical**. Every emitted file, including the
fingerprinted asset names, has to match.

Why this shape rather than "assert zero ``<table class=lntable>`` in the build":

* It needs no pinned reference content, so it runs on every PR in a few seconds.
* It is strictly stronger. A ``lntable`` grep only catches the one symptom that has
  already bitten us. An identity diff catches *any* structural leak of consumer config
  into theme output — a future ``markup.highlight`` key that changes emitted structure
  rather than emitted colour would be caught the day it is forwarded, with no new test.

See docs/contracts.md §3 ("Verified Hugo behaviour") and specs/007 §2 Layer 2.

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import difflib
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

# The hostile configuration. These are exactly the settings citizix ships today, and
# they are what puts a line-number gutter on a one-line `sudo dnf -y install redis`.
HOSTILE_ENV = {
    "HUGO_MARKUP_HIGHLIGHT_LINENOS": "true",
    "HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE": "true",
}

MAX_REPORTED_FILES = 5
MAX_DIFF_LINES = 40
# RSS and sitemap files put a whole page on one line. Untruncated they bury the signal.
MAX_DIFF_LINE_CHARS = 220


def resolve_theme(repo_root: Path):
    """Work out how to point Hugo at this checkout as a theme.

    ``exampleSite/hugo.toml`` declares ``theme = "hugo-theme-runbook"``, so Hugo looks
    for a directory of that name inside ``--themesDir``. On a GitHub runner the default
    checkout path already ends in the repository name, so ``--themesDir ..`` happens to
    work — but it silently breaks in a git worktree, a renamed clone, or a fork with a
    different repo name.

    Passing ``--themesDir <parent>`` together with ``--theme <basename>`` works in every
    one of those cases without a symlink and without editing exampleSite/hugo.toml
    (owned by another workstream — docs/contracts.md §1).
    """
    return repo_root.parent.resolve(), repo_root.name


def build(repo_root: Path, dest: Path, extra_env=None, strict=False, quiet=False, hugo="hugo"):
    themes_dir, theme = resolve_theme(repo_root)
    cmd = [
        hugo,
        "--source", str(repo_root / "exampleSite"),
        "--themesDir", str(themes_dir),
        "--theme", theme,
        "--destination", str(dest),
        "--cleanDestinationDir",
        # Match what CI ships. --minify changes the emitted markup (unquoted attributes,
        # collapsed whitespace), so diffing unminified output would compare something
        # nobody deploys.
        "--gc", "--minify",
    ]
    if strict:
        cmd += ["--panicOnWarning", "--printPathWarnings"]

    env = dict(os.environ)
    # Do not let an ambient hostile setting contaminate the *baseline* build.
    for key in HOSTILE_ENV:
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)

    if not quiet:
        shown = " ".join(f"{k}={v}" for k, v in sorted((extra_env or {}).items()))
        print(f"  $ {shown + ' ' if shown else ''}hugo --source exampleSite …", flush=True)

    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"FAIL: hugo build failed for {dest} (exit {proc.returncode})")
    return proc.stdout


def walk(root: Path):
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
    }


def excerpt_diff(a: Path, b: Path) -> str:
    try:
        left = a.read_text(encoding="utf-8").splitlines()
        right = b.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return "    (binary or unreadable file)"
    lines = list(difflib.unified_diff(left, right, "baseline", "hostile", lineterm="", n=1))
    if len(lines) > MAX_DIFF_LINES:
        lines = lines[:MAX_DIFF_LINES] + [f"… {len(lines) - MAX_DIFF_LINES} more diff lines"]
    clipped = [
        line if len(line) <= MAX_DIFF_LINE_CHARS
        else line[:MAX_DIFF_LINE_CHARS] + f" …[+{len(line) - MAX_DIFF_LINE_CHARS} chars]"
        for line in lines
    ]
    return "\n".join("    " + line for line in clipped)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="theme repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="where to put the two builds (default: <repo-root>/public-reqcb1)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="keep both build trees for inspection instead of deleting them",
    )
    parser.add_argument(
        "--hugo",
        default=os.environ.get("RB_HUGO", "hugo"),
        help="hugo binary to use (or set RB_HUGO). Handy for reproducing the CI matrix "
             "locally against the 0.146.0 floor as well as latest.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if not (repo_root / "exampleSite" / "hugo.toml").is_file():
        return fail(f"no exampleSite/hugo.toml under {repo_root}")
    hugo = args.hugo
    if shutil.which(hugo) is None and not Path(hugo).is_file():
        return fail(f"{hugo} is not on PATH")

    work = (args.work_dir or repo_root / "public-reqcb1").resolve()
    baseline = work / "baseline"
    hostile = work / "hostile"

    print("REQ-CB-1 — line-number config must not leak from site config into theme output")
    build(repo_root, baseline, strict=True, hugo=hugo)
    build(repo_root, hostile, extra_env=HOSTILE_ENV, hugo=hugo)

    left, right = walk(baseline), walk(hostile)
    problems = []

    for missing in sorted(right - left):
        problems.append((missing, "only in the hostile build"))
    for missing in sorted(left - right):
        problems.append((missing, "only in the baseline build"))

    shared = sorted(left & right)
    _, mismatch, errors = filecmp.cmpfiles(baseline, hostile, shared, shallow=False)
    for rel in sorted(mismatch):
        problems.append((rel, "contents differ"))
    for rel in sorted(errors):
        problems.append((rel, "could not be compared"))

    if not problems:
        print(f"  {len(shared)} files compared, byte-identical")
        print("PASS: REQ-CB-1 — hostile line-number config produced no output change")
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
        return 0

    print()
    print(f"FAIL: {len(problems)} file(s) changed when the site forced line numbers on.")
    print("      The render hook is forwarding markup.highlight config it must override.")
    print("      Read layouts/_markup/render-codeblock.html and specs/004 §2.")
    print()
    for rel, why in problems[:MAX_REPORTED_FILES]:
        print(f"  {rel}: {why}")
        if why == "contents differ":
            print(excerpt_diff(baseline / rel, hostile / rel))
    if len(problems) > MAX_REPORTED_FILES:
        print(f"  … and {len(problems) - MAX_REPORTED_FILES} more")
    print()
    print(f"Both build trees kept at {work} for inspection.")
    return 1


def fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
