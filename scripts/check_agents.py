#!/usr/bin/env python3
"""Agent configuration is consistent — issue #40.

This repository gates seven things about the theme it ships and, until this file,
nothing about the configuration those gates run under. That asymmetry produced two
defects in the working tree within a day of the tooling being copied:

  * `.agents/skills/gates/SKILL.md` read `.Codex/hooks/` — a find-and-replace artefact
    of a byte copy. It resolves on a case-insensitive macOS filesystem and not on the
    Linux runner, so it would have shipped green and failed for the next contributor.
  * `.codex/hooks.json` hard-coded `/Users/<someone>/Code/my/hugo-theme-runbook/…`.
    `.gitignore` already refuses exactly this for `settings.local.json`, in its own
    words: "puts one contributor's laptop into everyone's config."

Both are the same shape as the theme's own traps — silent, green, and wrong in a
different checkout. So they get the same treatment: a gate that fails the pull request.

    .claude/ and .mcp.json are CANONICAL.  .codex/ is a MIRROR.  .agents/ is a symlink.

The direction of repair is one-way and every check's remedy says so: fix the mirror,
never weaken the canonical side. `--fix` repairs only what is mechanically derivable
(the symlink, the executable bit). Anything needing judgement — an MCP server, a hook
registration — is reported for a human or an agent to resolve, because a script that
guesses at those would paper over the disagreement rather than surface it.

Standard library only, no `tomllib`, and no PyYAML (ADR-1). `tomllib` is 3.11+ and this
has to run on whatever python3 a contributor has; the Codex config is read with regexes
over its text, which is enough to compare a mirror against its source. The frontmatter
parser is a flat `key: value` splitter because every skill, subagent and command in this
repo uses scalar frontmatter only.

    python3 scripts/check_agents.py          check only, exit 1 on any problem
    python3 scripts/check_agents.py --fix    repair what is derivable, then check

Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLAUDE = ROOT / ".claude"
CODEX = ROOT / ".codex"
AGENTS = ROOT / ".agents"
MCP_JSON = ROOT / ".mcp.json"
SETTINGS = CLAUDE / "settings.json"
CODEX_CONFIG = CODEX / "config.toml"
CODEX_HOOKS = CODEX / "hooks.json"

# A skill description is loaded in EVERY session of EVERY client sharing .claude/skills,
# whether or not the skill is used. It is a routing hint — when to reach for this — and
# the procedure belongs in the body. The budget is stated in .claude/AGENTS.md.
MAX_SKILL_DESCRIPTION = 400

problems: list[str] = []
fixed: list[str] = []
notes: list[str] = []


def problem(check: str, msg: str, remedy: str = "") -> None:
    problems.append(f"{check}: {msg}" + (f"\n      → {remedy}" if remedy else ""))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# ── parsing ─────────────────────────────────────────────────────────────────────────


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        problem("config", f"{rel(path)} is missing")
    except json.JSONDecodeError as exc:
        problem("config", f"{rel(path)} is not valid JSON: {exc}")
    return None


def frontmatter(path: Path) -> "tuple[dict, str]":
    """Split a `---` frontmatter block from the body. Scalar keys only — see the docstring."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block, body = text[3:end], text[end + 4:]
    meta = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line[0].isspace():          # nested value; this repo does not use one
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip("'\"")
    return meta, body.lstrip("\n")


def toml_tables(text: str, prefix: str) -> "dict[str, str]":
    """Return {name: body} for every `[prefix.name]` table, up to the next table header."""
    out = {}
    pattern = re.compile(r"^\[" + re.escape(prefix) + r"\.([A-Za-z0-9_-]+)\]\s*$", re.M)
    marks = list(pattern.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        nxt = re.search(r"^\[", text[m.end():end], re.M)
        body = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():end]
        out[m.group(1)] = body
    return out


def toml_value(body: str, key: str):
    """Read a scalar string or a flat array of strings out of a table body."""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    if not m:
        return None
    raw = m.group(1)
    if raw.startswith("["):
        depth, buf = 0, ""
        for chunk in body[body.index(raw):].splitlines():
            buf += chunk
            depth += chunk.count("[") - chunk.count("]")
            if depth <= 0:
                break
        return re.findall(r'"((?:[^"\\]|\\.)*)"', buf)
    m2 = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', raw)
    return m2.group(1) if m2 else raw


# ── checks ──────────────────────────────────────────────────────────────────────────


def check_skills_symlink(fix: bool) -> None:
    """One copy of the skills, not one per client. A copy drifts; this one already did."""
    link = AGENTS / "skills"
    want = "../.claude/skills"
    if link.is_symlink() and Path(os.readlink(link)) == Path(want):
        return
    if fix and not link.is_symlink() and not link.exists():
        link.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(want, link)
        fixed.append(f"created {rel(link)} -> {want}")
        return
    if not link.is_symlink():
        problem(
            "skills",
            f"{rel(link)} is {'a directory of copies' if link.is_dir() else 'missing'}, not a symlink",
            f"Run: rm -rf {rel(link)} && ln -s {want} {rel(link)}",
        )
        return
    problem("skills", f"{rel(link)} points at {os.readlink(link)}, expected {want}")


def check_skills() -> None:
    skills = CLAUDE / "skills"
    if not skills.is_dir():
        problem("skills", f"{rel(skills)} is missing")
        return
    for skill in sorted(p for p in skills.iterdir() if p.is_dir()):
        md = skill / "SKILL.md"
        if not md.exists():
            problem("skills", f"{rel(skill)} has no SKILL.md")
            continue
        meta, body = frontmatter(md)
        name = meta.get("name")
        if not name:
            problem("skills", f"{rel(md)} has no `name` in its frontmatter")
        elif name != skill.name:
            problem("skills", f"{rel(md)} declares name '{name}' but lives in '{skill.name}/'")
        description = meta.get("description", "")
        if not description:
            problem("skills", f"{rel(md)} has no `description` — the model cannot route to it")
        elif len(description) > MAX_SKILL_DESCRIPTION:
            problem(
                "skills",
                f"{rel(md)} description is {len(description)} chars (max {MAX_SKILL_DESCRIPTION})",
                "It is a routing hint loaded in every session, not documentation — "
                "move the detail into the body. See .claude/AGENTS.md.",
            )
        if not body.strip():
            problem("skills", f"{rel(md)} has an empty body")


def check_subagents() -> None:
    agents_dir = CLAUDE / "agents"
    if not agents_dir.is_dir():
        notes.append("no .claude/agents/ — subagents are optional")
        return
    for md in sorted(agents_dir.glob("*.md")):
        meta, body = frontmatter(md)
        name = meta.get("name")
        if not name:
            problem("subagents", f"{rel(md)} has no `name` in its frontmatter")
        elif name != md.stem:
            problem("subagents", f"{rel(md)} declares name '{name}' but the file is '{md.name}'")
        if not meta.get("description"):
            problem("subagents", f"{rel(md)} has no `description` — nothing can route to it")
        if not body.strip():
            problem("subagents", f"{rel(md)} has an empty body")
        # A subagent that can write is a subagent that can bypass the guardrail hook's
        # review, because it runs in its own context with its own tool grants.
        tools = meta.get("tools", "")
        for writer in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            if re.search(rf"\b{writer}\b", tools):
                problem(
                    "subagents",
                    f"{rel(md)} grants `{writer}` — the subagents here are read-only by design",
                    "Report findings to the caller and let it make the edit. See .claude/AGENTS.md.",
                )


def check_commands() -> None:
    commands = CLAUDE / "commands"
    if not commands.is_dir():
        notes.append("no .claude/commands/ — slash commands are optional")
        return
    for cmd in sorted(commands.glob("*.md")):
        meta, body = frontmatter(cmd)
        if not meta.get("description"):
            problem("commands", f"{rel(cmd)} has no `description` — it is unlabelled in /help")
        if not body.strip():
            problem("commands", f"{rel(cmd)} has an empty body")


def hooks_in(payload) -> "set[str]":
    """Every .claude/hooks/<script> named by a settings-shaped hooks block."""
    found = set()
    for groups in (payload.get("hooks") or {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                found.update(re.findall(r"\.claude/hooks/([A-Za-z0-9_.-]+\.py)", hook.get("command", "")))
    return found


def check_hooks(settings: dict, fix: bool) -> None:
    """The scripts are shared, never copied. Only the registration is mirrored."""
    hooks_dir = CLAUDE / "hooks"
    if not hooks_dir.is_dir():
        problem("hooks", f"{rel(hooks_dir)} is missing")
        return

    on_disk = {p.name for p in hooks_dir.glob("*.py") if not p.name.startswith("test_")}
    by_claude = hooks_in(settings)
    codex_payload = read_json(CODEX_HOOKS) if CODEX_HOOKS.exists() else {}
    by_codex = hooks_in(codex_payload or {})

    for name in sorted(by_claude - on_disk):
        problem("hooks", f".claude/settings.json registers {name}, which does not exist")
    for name in sorted(by_codex - on_disk):
        problem("hooks", f"{rel(CODEX_HOOKS)} registers {name}, which does not exist")
    for name in sorted(on_disk - by_claude):
        problem("hooks", f"{name} exists but nothing registers it — an unregistered hook never runs")
    for name in sorted(by_claude - by_codex):
        problem(
            "hooks",
            f"{name} runs under Claude Code but not Codex",
            f"Register it in {rel(CODEX_HOOKS)} too — point at .claude/hooks/, never a copy.",
        )
    for name in sorted(by_codex - by_claude):
        problem("hooks", f"{name} runs under Codex but not Claude Code")

    # A copy of a hook is the bug this whole gate exists for.
    for stray in sorted((CODEX / "hooks").glob("*.py")) if (CODEX / "hooks").is_dir() else []:
        problem(
            "hooks",
            f"{rel(stray)} is a copy of a shared hook",
            "Delete it and register .claude/hooks/ from the Codex config instead.",
        )

    for name in sorted(on_disk & by_claude):
        script = hooks_dir / name
        if not os.access(script, os.X_OK):
            if fix:
                script.chmod(script.stat().st_mode | 0o111)
                fixed.append(f"chmod +x {rel(script)}")
            else:
                problem("hooks", f"{rel(script)} is not executable", f"Run: chmod +x {rel(script)}")


def check_mcp_mirror(codex_config: str) -> None:
    """Names AND definitions. Comparing only names lets the two drift on args, which is
    where a version pin lives."""
    mcp = read_json(MCP_JSON) or {}
    declared = mcp.get("mcpServers") or {}
    mirrored = toml_tables(codex_config, "mcp_servers")

    for name in sorted(set(declared) - set(mirrored)):
        spec = declared[name]
        args = ", ".join(f'"{a}"' for a in spec.get("args", []))
        problem(
            "mcp",
            f".mcp.json declares the '{name}' server and the Codex config does not",
            f'Add:  [mcp_servers.{name}]\\n        command = "{spec.get("command", "")}"\\n        args = [{args}]',
        )
    for name in sorted(set(mirrored) - set(declared)):
        problem("mcp", f"the Codex config declares the '{name}' server and .mcp.json does not")

    for name in sorted(set(declared) & set(mirrored)):
        want, got = declared[name], mirrored[name]
        if want.get("command") and toml_value(got, "command") != want["command"]:
            problem(
                "mcp",
                f"'{name}' runs {toml_value(got, 'command')!r} under Codex "
                f"and {want['command']!r} under Claude Code",
            )
        if list(want.get("args") or []) != list(toml_value(got, "args") or []):
            problem(
                "mcp",
                f"'{name}' args differ between .mcp.json and the Codex config — "
                "that is where a version pin lives",
                f"Codex has {toml_value(got, 'args')}, .mcp.json has {want.get('args')}",
            )


def check_no_absolute_paths() -> None:
    """A machine-specific path in shared config is one contributor's laptop in everyone's
    checkout — the rule .gitignore already states for settings.local.json."""
    targets: "list[Path]" = [SETTINGS, MCP_JSON]
    for base, patterns in (
        (CLAUDE, ("agents/*.md", "commands/*.md", "skills/*/SKILL.md", "hooks/*.py", "*.md", "*.json")),
        (CODEX, ("*.toml", "*.json", "agents/*.toml", "rules/*", "*.md")),
        (AGENTS, ("*.md",)),
    ):
        for pattern in patterns:
            targets.extend(base.glob(pattern))

    bad = re.compile(r"(?<!\.)/(?:Users|home)/[A-Za-z0-9._-]+/")
    for path in sorted(set(targets)):
        if not path.is_file() or path.name == "settings.local.json":
            continue
        for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            # `/Users/...` with a literal ellipsis is how the docs quote the wrong
            # spelling in order to warn about it. Same exemption the guardrail hook
            # gives a heredoc body: text about a mistake is not the mistake.
            if bad.search(line) and "/Users/..." not in line and "/home/..." not in line:
                problem(
                    "portability",
                    f"{rel(path)}:{lineno} contains a machine-specific absolute path",
                    "Use a repo-relative path, or resolve the root at run time: "
                    "bash -c 'exec python3 \"$(git rev-parse --show-toplevel)/…\"'",
                )


def check_case_sensitivity() -> None:
    """The `.Codex` bug. A path that differs only in case resolves on macOS and fails on
    the Linux runner, so it cannot be caught by running the command locally."""
    real = {p.name for p in ROOT.iterdir()}
    lower = {name.lower(): name for name in real}
    pattern = re.compile(r"(?<![\w./-])(\.[A-Za-z][A-Za-z0-9_-]*)/")
    for base in (CLAUDE, CODEX, AGENTS):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in (".md", ".json", ".toml", ".py"):
                continue
            for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                for ref in set(pattern.findall(line)):
                    canonical = lower.get(ref.lower())
                    if canonical and canonical != ref:
                        problem(
                            "portability",
                            f"{rel(path)}:{lineno} refers to '{ref}/', but the directory is '{canonical}/'",
                            "It resolves on a case-insensitive filesystem and fails on the CI runner.",
                        )


def check_documented_numbers() -> None:
    """A number duplicated into prose that no gate reads goes stale — it did, in five
    files, the day check_contrast.py went from 150 assertions to 156."""
    gate = ROOT / "scripts" / "check_contrast.py"
    if not gate.exists():
        return
    try:
        out = subprocess.run(
            [sys.executable, str(gate)], cwd=ROOT, capture_output=True, text=True, timeout=120
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        notes.append(f"could not run check_contrast.py to verify documented counts: {exc}")
        return
    m = re.search(r"(\d+)\s+assertions", out)
    if not m:
        notes.append("check_contrast.py printed no assertion count to compare against")
        return
    actual = m.group(1)

    quoted = re.compile(r"(\d+)\s+(?:assertions|ratios|contrast assertions)")
    for path in sorted(ROOT.glob("*.md")) + sorted(ROOT.glob("docs/*.md")) + \
            sorted(CLAUDE.rglob("*.md")):
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for found in quoted.findall(line):
                if found != actual:
                    problem(
                        "docs",
                        f"{rel(path)}:{lineno} says {found} contrast assertions; "
                        f"check_contrast.py reports {actual}",
                        f"Update the number, or stop quoting it. Line: {line.strip()[:80]}",
                    )


def check_tooling_docs() -> None:
    for path in (CLAUDE / "AGENTS.md", CODEX / "AGENTS.md", AGENTS / "AGENTS.md"):
        if not path.exists():
            problem("docs", f"{rel(path)} is missing — the sync map has nowhere to live")


# ── report ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fix", action="store_true",
                        help="repair what is mechanically derivable, then check")
    args = parser.parse_args()

    settings = read_json(SETTINGS) or {}
    codex_config = CODEX_CONFIG.read_text() if CODEX_CONFIG.exists() else ""
    if not codex_config:
        problem("config", f"{rel(CODEX_CONFIG)} is missing — Codex gets no project configuration")

    print("Agent configuration — .claude/ and .mcp.json are canonical, .codex/ mirrors them")

    check_skills_symlink(args.fix)
    check_skills()
    check_subagents()
    check_commands()
    check_hooks(settings, args.fix)
    check_mcp_mirror(codex_config)
    check_no_absolute_paths()
    check_case_sensitivity()
    check_documented_numbers()
    check_tooling_docs()

    for item in fixed:
        print(f"  [fix ] {item}")
    for item in notes:
        print(f"  [note] {item}")

    if problems:
        print(f"\n  {len(problems)} problem(s)\n")
        for item in problems:
            print(f"  ✗ {item}")
        print("\nThe repair direction is one-way: fix the mirror, never weaken the canonical")
        print("side. See .claude/AGENTS.md for the sync map.")
        print("FAIL: agent configuration")
        return 1

    print("  every mirror agrees with its source, no machine-specific paths, no case drift")
    print("PASS: agent configuration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
