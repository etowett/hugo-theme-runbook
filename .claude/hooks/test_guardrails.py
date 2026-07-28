#!/usr/bin/env python3
"""Tests for the guardrail hook.

A hook with false positives gets switched off, and a hook that is switched off is worse
than no hook because everyone still believes it is running. So the cases below are half
"this must fire" and half "this must NOT fire" — including, in the last test, **every
file currently in the repository**, replayed through the hook as if an agent had just
written it. If any rule fires on the tree as it stands today, that rule is wrong.

    python3 .claude/hooks/test_guardrails.py

Standard library only (ADR-1), same as every other script here.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = pathlib.Path(__file__).with_name("guardrails.py")
ROOT = HOOK.parent.parent.parent


def run(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def bash(command: str) -> subprocess.CompletedProcess:
    return run({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "cwd": str(ROOT), "tool_input": {"command": command}})


def write(path: str, content: str) -> subprocess.CompletedProcess:
    return run({"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(ROOT),
                "tool_input": {"file_path": str(ROOT / path), "content": content}})


class Blocks(unittest.TestCase):
    def assertBlocked(self, res, rule):
        self.assertEqual(res.returncode, 2, f"expected a block, got {res.returncode}\n{res.stderr}")
        self.assertIn(rule, res.stderr)

    def assertAllowed(self, res):
        self.assertEqual(res.returncode, 0, f"unexpected block:\n{res.stderr}")

    # R1 — the themesDir spelling that only works by coincidence
    def test_themesdir_relative_is_blocked(self):
        self.assertBlocked(bash("hugo --source exampleSite --themesDir ../.. --panicOnWarning"), "R1")

    def test_themesdir_dirname_basename_is_fine(self):
        self.assertAllowed(bash(
            'hugo --source exampleSite --themesDir "$(dirname "$PWD")" '
            '--theme "$(basename "$PWD")" --panicOnWarning'))

    def test_a_heredoc_may_quote_the_wrong_command(self):
        # Regression, 2026-07-28: writing the issue that PROPOSED this hook was blocked by
        # it, because the body quotes `--themesDir ../..` in order to warn about it. Every
        # doc, spec, issue and PR body in this repository does the same thing.
        self.assertAllowed(bash(
            "gh issue create --body-file - <<'EOF'\n"
            "`--themesDir ../..` fails in a worktree; a build without --panicOnWarning\n"
            "exits 0 on a missing layout, and `gzip -9` without -n makes budgets flaky.\n"
            "EOF"))

    def test_a_real_command_after_a_heredoc_is_still_checked(self):
        self.assertBlocked(bash(
            "cat <<'EOF' > notes.md\nharmless prose\nEOF\n"
            "hugo --source exampleSite --themesDir ../.. --panicOnWarning"), "R1")

    # R2 — --panicOnWarning
    def test_build_without_panic_on_warning_is_blocked(self):
        self.assertBlocked(bash("hugo --source exampleSite --destination public"), "R2")

    def test_hugo_version_is_not_a_build(self):
        self.assertAllowed(bash("hugo version"))

    def test_hugo_mod_is_not_a_build(self):
        self.assertAllowed(bash("hugo mod graph"))

    def test_help_is_not_a_build(self):
        # Regression: `hugo build --help` was read as a build and blocked, 2026-07-28.
        for cmd in ("hugo build --help", "hugo --help", "hugo -h", "hugo server --help"):
            with self.subTest(cmd=cmd):
                self.assertAllowed(bash(cmd))

    def test_hugo_named_after_a_pipe_is_not_a_second_build(self):
        self.assertAllowed(bash("hugo mod graph | grep hugo-theme-runbook"))

    def test_unused_templates_build_is_exempt(self):
        # Regression, 2026-07-28: ci.yml runs --printUnusedTemplates as its OWN step,
        # deliberately without --panicOnWarning, because it warns once per unreached
        # template. Requiring the flag here would make the documented recipe unrunnable.
        self.assertAllowed(bash(
            'hugo --source exampleSite --themesDir "$(dirname "$PWD")" '
            '--theme "$(basename "$PWD")" --destination "$PWD/public-unused" '
            "--cleanDestinationDir --printUnusedTemplates"))

    def test_bare_hugo_is_a_build(self):
        self.assertBlocked(bash("hugo"), "R2")

    def test_hugo_build_subcommand_is_a_build(self):
        self.assertBlocked(bash("hugo build --minify"), "R2")

    def test_hugo_server_warns_but_does_not_block(self):
        res = bash('hugo server --source exampleSite --themesDir "$(dirname "$PWD")" '
                   '--theme "$(basename "$PWD")" --disableFastRender')
        self.assertAllowed(res)
        self.assertIn("R2", res.stdout)

    # R3 — gzip reproducibility
    def test_gzip_without_n_is_blocked(self):
        self.assertBlocked(bash("gzip -9 -c public/index.html | wc -c"), "R3")

    def test_gzip_with_n_is_fine(self):
        self.assertAllowed(bash("gzip -n -9 -c public/index.html | wc -c"))

    def test_combined_gzip_flags_are_fine(self):
        self.assertAllowed(bash("gzip -n9c public/index.html | wc -c"))

    # R4 — ADR-1
    def test_npm_install_is_blocked(self):
        self.assertBlocked(bash("npm install sass"), "R4")

    def test_pip_install_is_blocked(self):
        self.assertBlocked(bash("pip install beautifulsoup4"), "R4")

    def test_npx_playwright_is_sanctioned(self):
        self.assertAllowed(bash("npx playwright test --config .github/visual/playwright.config.mjs"))

    # R5 — never commit to main. Only meaningful when the checkout is on main.
    def test_commit_rule_matches_current_branch(self):
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=str(ROOT),
                                capture_output=True, text=True).stdout.strip()
        res = bash('git commit -m "wip"')
        if branch in ("main", "master"):
            self.assertBlocked(res, "R5")
        else:
            self.assertAllowed(res)

    # R5, the worktree case. docs/contracts.md §0 runs four workstreams in parallel and a
    # git worktree is how: the repository root stays on `main` while the work happens on a
    # feature branch somewhere else. R5 used to read the branch of the hook's cwd, so it
    # blocked every commit made from a worktree — and, the same bug the other way, waved
    # through a `cd <root> && git commit` issued from a worktree while genuinely on main.
    # Both directions are asserted here because a rule that only fails safe is still wrong.
    def _worktree(self):
        out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=str(ROOT),
                             capture_output=True, text=True).stdout
        entries, cur = [], {}
        for line in out.splitlines():
            if line.startswith("worktree "):
                cur = {"path": line.split(" ", 1)[1]}
                entries.append(cur)
            elif line.startswith("branch "):
                cur["branch"] = line.split(" ", 1)[1]
        for e in entries:
            if e["path"] != str(ROOT) and e.get("branch", "").rsplit("/", 1)[-1] not in ("main", "master"):
                return e["path"]
        return None

    def test_commit_in_a_worktree_reads_the_worktree_branch(self):
        wt = self._worktree()
        if wt is None:
            self.skipTest("no feature-branch worktree checked out to test against")
        self.assertAllowed(bash(f'cd {wt} && git commit -m "wip"'))
        self.assertAllowed(bash(f'git -C {wt} commit -m "wip"'))

    # A repository ON MAIN, built here rather than borrowed from the checkout.
    #
    # This used to read ROOT's branch and skipTest when it was not main — which is to
    # say it ran in exactly the state where you are not allowed to commit, and skipped
    # in the state where you are. It was therefore green on every feature branch while
    # `git -C <main-checkout> push` went straight through R5, and it only spoke up
    # after that fix had already been merged. A test that opts out on the branch you
    # develop on is not protecting anything.
    def _repo_on_main(self):
        d = tempfile.mkdtemp(prefix="rb-guard-main-")
        run = lambda *a: subprocess.run(a, cwd=d, capture_output=True, text=True)
        run("git", "init", "-q", "-b", "main", ".")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        pathlib.Path(d, "f").write_text("x")
        run("git", "add", "f")
        run("git", "-c", "commit.gpgsign=false", "commit", "-qm", "init")
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def test_a_checkout_on_main_is_blocked_however_the_command_reaches_it(self):
        m = self._repo_on_main()
        # The form that always worked.
        self.assertBlocked(bash(f'cd {m} && git commit -m "wip"'), "R5")
        # `git -C` — how you commit to a DIFFERENT checkout, and the form that
        # bypassed R5 entirely because the subcommand is not adjacent to `git`.
        self.assertBlocked(bash(f'git -C {m} commit -m "wip"'), "R5")
        self.assertBlocked(bash(f'git -C {m} push'), "R5")
        # A global option before the subcommand must not disable the rule either.
        self.assertBlocked(bash(f'git --no-pager -C {m} push'), "R5")
        self.assertBlocked(bash(f'cd {m} && git -c user.name=x commit -m "wip"'), "R5")

    def test_a_git_subcommand_that_merely_mentions_commit_is_not_blocked(self):
        # The widened trigger must not start blocking reads. `log` is neither an
        # option nor commit|push, so the alternation is never reached.
        m = self._repo_on_main()
        self.assertAllowed(bash(f'git -C {m} log --grep commit'))
        self.assertAllowed(bash(f'git -C {m} log --oneline'))

    def test_a_cd_to_somewhere_that_is_not_a_directory_falls_back_to_cwd(self):
        # A typo in the path must not silently disable the rule.
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=str(ROOT),
                                capture_output=True, text=True).stdout.strip()
        res = bash('cd /no/such/place && git commit -m "wip"')
        if branch in ("main", "master"):
            self.assertBlocked(res, "R5")
        else:
            self.assertAllowed(res)

    # R7 — ADR-0
    def test_legacy_default_layout_is_blocked(self):
        self.assertBlocked(write("layouts/_default/single.html", "<p>x</p>"), "R7")

    def test_legacy_partials_dir_is_blocked(self):
        self.assertBlocked(write("layouts/partials/head.html", "<meta>"), "R7")

    def test_modern_partials_dir_is_fine(self):
        self.assertAllowed(write("layouts/_partials/head/new.html", "<meta>"))

    def test_shortcodes_dir_is_fine(self):
        # layouts/shortcodes/ is what this repository ships and what it builds green with.
        self.assertAllowed(write("layouts/shortcodes/note.html", "<aside>{{ .Inner }}</aside>"))

    # R8 — showcase screenshots stay absent until M6
    def test_screenshot_placeholder_is_blocked(self):
        self.assertBlocked(write("images/screenshot.png", "not-really-a-png"), "R8")

    # R9 — the boolean default trap
    def test_default_true_in_a_layout_is_blocked(self):
        self.assertBlocked(
            write("layouts/_partials/utils/settings.html",
                  '{{ $showLastmod := $rb.showLastmod | default true }}'), "R9")

    def test_default_true_inside_a_template_comment_is_not_a_use(self):
        self.assertAllowed(write(
            "layouts/_partials/utils/settings.html",
            '{{- /* `| default true` is a bug for any boolean whose default is true. */ -}}\n'
            '{{- $x := true -}}{{ if isset $rb "x" }}{{ $x = $rb.x }}{{ end }}'))

    def test_default_on_a_string_is_fine(self):
        self.assertAllowed(write("layouts/_partials/utils/settings.html",
                                 '{{ $d := $rb.dateFormat | default ":date_long" }}'))

    # R10 — configuration namespace
    def test_bare_top_level_param_is_blocked(self):
        self.assertBlocked(write("layouts/_partials/article/meta.html",
                                 "{{ site.Params.showAuthorBio }}"), "R10")

    def test_runbook_namespace_is_fine(self):
        self.assertAllowed(write("layouts/_partials/article/meta.html",
                                 "{{ site.Params.runbook.showLastmod }}"))

    def test_hugo_own_site_conventions_are_fine(self):
        self.assertAllowed(write("layouts/rss.xml",
                                 "{{ site.Params.mainSections }}{{ site.Params.description }}"))

    # Files outside layouts/ are not template-linted
    def test_docs_may_discuss_the_traps(self):
        self.assertAllowed(write("docs/configuration.md",
                                 "Do not write `x | default true`; use `site.Params.foo`."))


class CurrentTreeIsClean(unittest.TestCase):
    """Replay every tracked file through the hook. Nothing shipped today may trip a rule."""

    def test_no_rule_fires_on_any_tracked_file(self):
        tracked = subprocess.run(["git", "ls-files"], cwd=str(ROOT),
                                 capture_output=True, text=True, check=True).stdout.split()
        offenders = []
        for rel in tracked:
            path = ROOT / rel
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # the woff2 and the png
            res = write(rel, content)
            if res.returncode != 0:
                offenders.append(f"{rel}\n{res.stderr}")
        self.assertEqual(offenders, [], "guardrail fires on files already in the tree:\n"
                                        + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main(verbosity=2)
