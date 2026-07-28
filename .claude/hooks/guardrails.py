#!/usr/bin/env python3
"""PreToolUse guardrail — block Runbook's six silent traps before the edit lands.

Every rule here enforces something that is *already* written down in docs/contracts.md,
CONTRIBUTING.md or an ADR, and that CI already catches. The point is not to add policy.
The point is that CI catches them minutes later, in a different window, with an error
message that names a gate rather than the mistake — and by then an agent has usually
built three more things on top of the wrong assumption.

Design rules for this file, which are the whole reason it stays trustworthy:

  * **Every rule cites its source.** If you cannot point at the line in the specs that
    makes something wrong, it does not belong here.
  * **A false positive is a bug in the hook, not something to work around.** The rules
    below were each checked against the current tree and fire on none of it.
  * **Standard library only, like every other script in this repository** (ADR-1).
  * **Two severities.** BLOCK is for "this is silently wrong and CI will not tell you
    why". WARN is for "this is probably wrong" and never stops you.

Protocol — https://code.claude.com/docs/en/hooks
  stdin  : the PreToolUse payload, JSON
  exit 2 : block the call; stderr is shown to the model as the reason
  exit 0 : allow; stdout may carry {"systemMessage": "..."} to warn without blocking
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# ── helpers ─────────────────────────────────────────────────────────────────────────

BLOCK: list[str] = []
WARN: list[str] = []


def block(rule: str, why: str, instead: str) -> None:
    BLOCK.append(f"[{rule}] {why}\n  → {instead}")


def warn(rule: str, why: str, instead: str) -> None:
    WARN.append(f"[{rule}] {why}\n  → {instead}")


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1\s*\n.*?\n[ \t]*\2\b", re.DOTALL)


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies before matching. A heredoc body is data, not a command.

    This repository writes about its own traps constantly — CONTRIBUTING.md, the specs and
    every issue and pull-request body quote the wrong spelling in order to warn about it.
    Without this, `gh issue create <<'EOF' … --themesDir ../.. … EOF` is blocked for
    *documenting* the rule, which is the fastest way to teach someone to disable the hook.
    """
    return HEREDOC.sub("<<HEREDOC", command)


def strip_comments(text: str) -> str:
    """Drop Go-template comments, so a rule cannot fire on prose explaining the rule.

    utils/settings.html documents the `| default true` bug inside a {{- /* ... */ -}}
    block. Without this, the file that exists to prevent the trap would trip the hook
    that exists to prevent the trap.
    """
    return re.sub(r"\{\{-?\s*/\*.*?\*/\s*-?\}\}", "", text, flags=re.DOTALL)


# ── Bash rules ──────────────────────────────────────────────────────────────────────

# Subcommands that are not a site build. These take no --panicOnWarning and must not be
# nagged about it. `hugo` with no subcommand, and `hugo build`, ARE builds.
NOT_A_BUILD = {
    "version", "env", "config", "mod", "new", "gen", "completion", "help",
    "list", "convert", "import", "deploy", "check", "release", "unusedi18n",
}


def hugo_invocations(command: str) -> list[list[str]]:
    """Every `hugo …` call in a shell line, as token lists starting at `hugo`.

    Splitting on `hugo` rather than regex-matching the whole line is what keeps
    `hugo build --help` and `hugo mod graph | grep hugo` from being read as builds.
    """
    tokens = re.split(r"\s+", command.strip())
    out: list[list[str]] = []
    for i, tok in enumerate(tokens):
        if tok == "hugo" or tok.endswith("/hugo"):
            rest: list[str] = []
            for nxt in tokens[i + 1:]:
                if nxt in ("|", "&&", "||", ";", ">", ">>"):
                    break
                rest.append(nxt)
            out.append(rest)
    return out


def classify_hugo(args: list[str]) -> str:
    """'build' | 'server' | 'other'."""
    if any(a in ("--help", "-h", "--version") for a in args):
        return "other"
    sub = next((a for a in args if not a.startswith("-")), "")
    if sub == "server":
        return "server"
    if sub in NOT_A_BUILD:
        return "other"
    return "build"

# ADR-1: no toolchain. `npx playwright` is deliberately not in here — CONTRIBUTING.md
# sanctions it for the visual suite, and the browser is how two real code-block bugs
# were found.
TOOLCHAIN = re.compile(
    r"\b(?:npm\s+(?:i|install|ci|add)|yarn\s+add|pnpm\s+(?:i|install|add)|bun\s+(?:i|install|add)"
    r"|pip3?\s+install|poetry\s+add|uv\s+(?:pip\s+install|add))\b"
)


def current_branch(cwd: str) -> str:
    try:
        out = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, capture_output=True, text=True, timeout=5, check=False,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


# `cd /some/path && git commit …` and `git -C /some/path commit …` both commit somewhere
# other than the hook's cwd, and R5 used to ignore that. It matters because a git WORKTREE
# is the supported way to run the four parallel workstreams (docs/contracts.md §0): the
# repository root stays on main while the work happens on a feature branch in
# ../runbook-worktrees/<name>, so every `cd <worktree> && git commit` was blocked while
# genuinely on a feature branch — and, the other way round, a `cd <root> && git commit`
# issued from a worktree was waved through while genuinely on main. Same bug, both
# directions; resolving the target directory fixes both.
CD_PREFIX = re.compile(r"(?:^|[;&|]\s*)cd\s+(?:--\s+)?([^\s;&|]+)")
# `-C` is not necessarily adjacent to `git` either — `git --no-pager -C <path> push`.
# Requiring adjacency here made R5 fire and then resolve the WRONG directory, falling
# back to cwd and allowing the command. Scan to the end of the command segment instead;
# `[^;&|]` cannot cross into the next one, so `cd /a && git -C /b commit` still resolves
# /b rather than /a.
GIT_C = re.compile(r"\bgit\b[^;&|]*?\s-C\s+([^\s;&|]+)")


def git_target_dir(command: str, cwd: str) -> str:
    """The directory a git command in `command` will actually run in."""
    target = cwd
    for m in CD_PREFIX.finditer(command):
        target = os.path.expanduser(m.group(1).strip("\'\""))
    m = GIT_C.search(command)
    if m:
        target = os.path.expanduser(m.group(1).strip("\'\""))
    if not os.path.isabs(target):
        target = os.path.join(cwd, target)
    return target if os.path.isdir(target) else cwd


def check_bash(raw: str, cwd: str) -> None:
    command = strip_heredocs(raw)

    # ── R1 · the themesDir spelling ──────────────────────────────────────────────
    # CONTRIBUTING.md "Building it locally"; reproduced 2026-07-28: in a worktree whose
    # directory is not named `hugo-theme-runbook`, `--themesDir ../..` fails with
    # `module "hugo-theme-runbook" not found`. It resolves in a plain checkout only
    # because the checkout happens to sit in a directory with the repository's name.
    if re.search(r"--themesDir[= ]+\.\.(/\.\.)?(\s|$)", command):
        block(
            "R1 themesDir",
            "`--themesDir ../..` resolves only by coincidence of directory naming. It "
            "fails in a git worktree, a renamed clone and a renamed fork.",
            'hugo --source exampleSite --themesDir "$(dirname "$PWD")" '
            '--theme "$(basename "$PWD")" …   (CONTRIBUTING.md · docs/verification.md §1)',
        )

    # ── R2 · --panicOnWarning ────────────────────────────────────────────────────
    # specs/007 §3.5. Hugo logs a missing layout, a bad shortcode call and a deprecated
    # function at WARN and then exits 0.
    for args in hugo_invocations(command):
        kind = classify_hugo(args)
        if kind == "other" or "--panicOnWarning" in args:
            continue
        # `--printUnusedTemplates` warns once per unreached template, so under
        # --panicOnWarning the only way to go green is to delete every fallback the demo
        # site does not exercise. ci.yml runs it as its own step against a reasoned
        # allowlist for exactly that reason, and so must anyone reproducing it locally.
        if "--printUnusedTemplates" in args:
            continue
        if kind == "build":
            block(
                "R2 panicOnWarning",
                "a Hugo build without `--panicOnWarning` exits 0 on a missing layout, a "
                "shortcode called wrongly, or a deprecation — so a build that renders "
                "nothing useful is a green tick.",
                "add --panicOnWarning (and --printPathWarnings, as CI does), or run /gates",
            )
        else:
            warn(
                "R2 panicOnWarning",
                "`hugo server` without `--panicOnWarning` will not surface the warnings CI "
                "fails on.",
                "for a check use /gates; for a dev loop /serve adds --disableFastRender",
            )
        break

    # ── R3 · gzip reproducibility ────────────────────────────────────────────────
    # CONTRIBUTING.md "Two reproducibility rules that bite" — without -n gzip writes an
    # mtime into the header, byte counts move between runs and every budget gate is flaky.
    if re.search(r"\bgzip\b", command) and re.search(r"-[0-9]", command):
        flags = re.findall(r"(?<!\S)-(\w+)", command)
        if not any("n" in f for f in flags):
            block(
                "R3 gzip -n",
                "`gzip` without `-n` writes a modification timestamp into the header, so "
                "byte counts move between runs and every budget gate goes flaky.",
                "gzip -n -9 -c <file> | wc -c   (CONTRIBUTING.md)",
            )

    # ── R4 · ADR-1, no toolchain ─────────────────────────────────────────────────
    if TOOLCHAIN.search(command):
        block(
            "R4 ADR-1",
            "Runbook has no build toolchain and adding one is a design decision, not a "
            "convenience. Hugo assembles CSS and JS through its own pipeline; every gate "
            "is python3 and the standard library.",
            "solve it without the dependency, or open an issue proposing the ADR-1 "
            "amendment first. `npx playwright` for the visual suite is already sanctioned.",
        )

    # ── R5 · never commit to main ────────────────────────────────────────────────
    #
    # The subcommand is NOT always adjacent to `git`. Global options sit between them:
    # `git -C <path> commit`, `git --no-pager push`, `git -c user.name=x commit`. The
    # trigger used to be `\bgit\s+(commit|push)\b`, which matched none of those, so
    # every one of them bypassed R5 entirely — on any branch, including main.
    #
    # `git -C` is the pointed case, because it is exactly how you commit to a
    # DIFFERENT checkout: `git -C <main-checkout> push` issued from a worktree was
    # waved straight through. git_target_dir() below already knew how to resolve it;
    # the rule simply never reached that code.
    #
    # The option group is `-\S+` plus an OPTIONAL argument, so it covers both
    # `--no-pager` (no argument) and `-C <path>` (one). It cannot swallow a
    # subcommand, because `git log --grep commit` stops at `log` — not an option, and
    # not commit|push — and never reaches the alternation.
    # Deleting a remote branch is spelled with `push`, and it is the opposite of what
    # this rule guards: `git push origin --delete eutychus/foo` removes a merged feature
    # branch and cannot add a commit to anything. Tidying up after a merge is the most
    # common thing anyone does while standing on main, so blocking it trains people to
    # ignore the guard — which costs more than the rule earns.
    #
    # Narrow on purpose. `--delete`/`-d` with a refspec is unambiguous; a bare
    # `git push` while on main is not, and stays blocked.
    #
    # Judged PER SEGMENT, not across the whole line. Asking "does this command contain a
    # delete?" lets a real push ride along behind one —
    # `git push origin --delete old; git push` would have been waved through entirely.
    # Caught by its own regression case, which is why that case exists.
    # Resolution needs the text UP TO the writing segment, not the segment alone: in
    # `cd <repo> && git commit`, the `cd` lives in an earlier segment and is what decides
    # which repository is being written to. Dropping it sent the answer back to cwd and
    # unblocked the commonest form there is — caught by its own regression case.
    target, cursor = None, 0
    for seg in re.split(r"[;&|]+", command):
        end = command.index(seg, cursor) + len(seg) if seg else cursor
        cursor = end
        if not re.search(r"\bgit\s+(?:-\S+(?:\s+\S+)?\s+)*(commit|push)\b", seg):
            continue
        if re.search(r"\bgit\s+(?:-\S+(?:\s+\S+)?\s+)*push\b.*\s(?:--delete|-d)\b", seg):
            continue
        target = git_target_dir(command[:end], cwd)
        break

    if target is not None:
        branch = current_branch(target)
        if branch in ("main", "master"):
            block(
                "R5 branch",
                f"you are on `{branch}`. CONTRIBUTING.md: never commit to main — branch, "
                "then raise a pull request.",
                "git switch -c eutychus/<short-slug>",
            )

    # ── R6 · the parity job cannot be run locally ────────────────────────────────
    if re.search(r"\bcheck_parity\.py\b", command) and "--emit" not in command:
        warn(
            "R6 parity",
            "check_parity.py diffs manifests from the private reference archive. "
            ".github/workflows/parity.yml is workflow_dispatch/schedule only and cannot "
            "run from a PR or a fork.",
            "if you only need the manifest for a local build, use --emit / --manifests",
        )


# ── Write / Edit rules ──────────────────────────────────────────────────────────────

# `mainSections`, `description` and `author` are Hugo's own site-level conventions and
# are read on purpose (head/seo.html, head/schema.html, rss.xml, search.json).
# Everything else must live under params.runbook.* — contracts §2.4.
SITE_PARAM_ALLOWED = {"runbook", "mainSections", "description", "author"}
SITE_PARAM = re.compile(r"(?:\bsite|\.Site)\.Params\.([A-Za-z_][A-Za-z0-9_]*)")


def check_file_write(path: str, added: str) -> None:
    rel = os.path.relpath(path, os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    rel = rel.replace(os.sep, "/")

    # ── R7 · ADR-0, no legacy layout tree ────────────────────────────────────────
    # When layouts/_default/ exists beside the new tree, the legacy path wins SILENTLY.
    if re.match(r"layouts/(_default|partials)/", rel):
        legacy = rel.split("/")[1]
        modern = {"_default": "layouts/ root (page.html, home.html, list.html, …)",
                  "partials": "layouts/_partials/"}[legacy]
        block(
            "R7 ADR-0",
            f"`layouts/{legacy}/` is the pre-v0.146.0 layout tree. When it exists beside "
            "the new one, the legacy path wins silently — a change to the modern template "
            "then has no effect and nothing warns.",
            f"put it in {modern}   (specs/006 ADR-0 · CONTRIBUTING.md 'Adding a template')",
        )

    # ── R8 · screenshots are absent on purpose until M6 ──────────────────────────
    if re.match(r"images/(screenshot|tn)\.", rel):
        block(
            "R8 M6",
            "images/screenshot.* and images/tn.* are the last two TODOs in "
            "check_showcase.py and are deliberately absent. A placeholder turns the check "
            "green while the showcase entry shows a test rig.",
            "leave them out until the demo is deployed (specs/008 M6 · CONTRIBUTING.md "
            "'Screenshots for the showcase')",
        )

    if not rel.startswith("layouts/") or not added:
        return

    body = strip_comments(added)

    # ── R9 · `| default true` silently ignores a consumer's `false` ──────────────
    for match in re.finditer(r"\|\s*default\s+true\b", body):
        line = body[: match.start()].count("\n")
        text = body.splitlines()[line] if line < len(body.splitlines()) else ""
        if "{{" not in text:
            continue  # prose, not an expression
        block(
            "R9 isset",
            "`false | default true` evaluates to `true`, so this silently ignores every "
            "consumer who turns the feature off.",
            'resolve it with isset — {{- $x := true -}}{{ if isset $rb "x" }}'
            "{{ $x = $rb.x }}{{ end }} — and note that isset is case-sensitive while Hugo "
            "lower-cases every param key, so the probe is lower-case. See "
            "layouts/_partials/utils/settings.html",
        )
        break

    # ── R10 · configuration namespace ───────────────────────────────────────────
    for match in SITE_PARAM.finditer(body):
        key = match.group(1)
        if key in SITE_PARAM_ALLOWED:
            continue
        block(
            "R10 namespace",
            f"`site.Params.{key}` reads a bare top-level param. Nothing in Runbook is read "
            "from one, ever, so the theme can never collide with a consuming site's keys.",
            f"namespace it as params.runbook.{key[0].lower() + key[1:]} and resolve it in "
            "_partials/utils/settings.html, which is the single place configuration is "
            "read (contracts §2.4). A new setting also needs a default in the root "
            "hugo.toml and an entry in docs/configuration.md.",
        )
        break


# ── entry point ─────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never break the session over a payload we cannot parse

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()

    if tool in ("Bash", "BashOutput"):
        check_bash(tool_input.get("command", "") or "", cwd)
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = tool_input.get("file_path", "") or ""
        added = tool_input.get("content") or tool_input.get("new_string") or ""
        for edit in tool_input.get("edits") or []:
            added += "\n" + (edit.get("new_string") or "")
        if path:
            check_file_write(path, added)

    if BLOCK:
        print(
            "Runbook guardrail — blocked.\n\n"
            + "\n\n".join(BLOCK)
            + "\n\nThese rules live in .claude/hooks/guardrails.py and each one cites the "
            "spec that makes it a rule. If this fired on something legitimate, that is a "
            "bug in the hook: fix the rule, do not work around it.",
            file=sys.stderr,
        )
        return 2

    if WARN:
        json.dump({"systemMessage": "Runbook guardrail — " + "\n".join(WARN)}, sys.stdout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
