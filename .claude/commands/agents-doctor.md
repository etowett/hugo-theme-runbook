---
description: Check the agent configuration — skills, subagents, commands, hooks, MCP mirrors, portability — and repair whatever has drifted
argument-hint: "[--fix]"
allowed-tools: Bash(python3 scripts/check_agents.py*) Bash(ls *) Bash(chmod +x*) Bash(ln -s*) Bash(git status*) Bash(git diff*) Read Edit Write Grep Glob
---

# Agent configuration doctor

This repository gates seven things about the theme it ships. `scripts/check_agents.py` gates the
configuration those gates run under, because the same class of defect appeared there first: a
directory reference whose capitalisation matched no real directory, which resolves on a
case-insensitive filesystem and fails on the Linux runner, and a hard-coded home directory that put
one contributor's laptop into everyone's checkout. Both were silent, green, and wrong somewhere
else — the same shape as the theme's own traps, so they get the same treatment.

```
.claude/ and .mcp.json are CANONICAL.  .codex/ is a MIRROR.  .agents/skills is a symlink.
```

## 1 — run it

```bash
python3 scripts/check_agents.py
```

If `$ARGUMENTS` contains `--fix`, run `python3 scripts/check_agents.py --fix` instead. `--fix`
repairs only what is mechanically derivable — the `.agents/skills` symlink and the executable bit
on a registered hook. It deliberately will not invent an MCP server definition or a hook
registration, because a script that guesses at those papers over the disagreement instead of
surfacing it.

Read the output rather than the exit code alone: `[fix ]` lines say what it changed, `[note]` lines
are informational (an absent `.claude/agents/` or `.claude/commands/` is allowed), and every `✗`
line is prefixed with the check that raised it.

## 2 — what each prefix means and what to do

**`config:`** — a file the gate needs is missing or unparseable: `.claude/settings.json`,
`.mcp.json`, `.codex/hooks.json` invalid JSON, or `.codex/config.toml` absent so Codex gets no
project configuration. Fix the malformed file. Restore a missing mirror file from its canonical
counterpart; never delete the canonical side to make the pair agree.

**`skills:`** — one of:
- `.agents/skills` is missing, or is a directory of copies rather than a symlink, or points
  somewhere other than `../.claude/skills`. One copy of the skills, not one per client — a copy
  drifts, and this one already did. `--fix` creates it when absent; otherwise remove it and relink
  as the remedy line spells out.
- a skill directory has no `SKILL.md`, its frontmatter has no `name`, or the `name` does not equal
  the directory it lives in. Rename the value, not the directory, unless the directory name is the
  wrong one.
- no `description`, or one over the character budget. The description is a routing hint loaded in
  **every** session of every client sharing the skills, whether or not the skill is used — move the
  procedure into the body rather than raising the budget.
- an empty body. A skill with nothing in it routes work to nowhere.

**`subagents:`** — a file in `.claude/agents/` whose `name` does not equal its filename stem,
which has no `description` so nothing can route to it, which has an empty body, or which grants
`Edit`, `Write`, `MultiEdit` or `NotebookEdit`. **The subagents here are read-only by design:** a
subagent runs in its own context with its own tool grants, so one that can write bypasses the
review the guardrail hook exists to perform. The repair is to remove the writing tool and have the
subagent report findings to its caller, never to relax the check.

**`commands:`** — a file in `.claude/commands/` with no `description`, which leaves it unlabelled
in `/help`, or with an empty body. Both are a one-line fix in the command file.

**`hooks:`** — the scripts are shared and only the *registration* is mirrored:
- registered but not on disk — create the script, or drop the registration.
- on disk but registered nowhere — an unregistered hook never runs, which is the worst of both
  outcomes. Register it or delete it deliberately.
- registered under one client and not the other — add the matching entry to the mirror, pointing at
  the shared `.claude/hooks/` path.
- a `.py` file under `.codex/hooks/` — that is a copy of a shared hook and is the exact bug this
  gate was written for. Delete it and register the shared script from the Codex config.
- not executable — `chmod +x`, or re-run with `--fix`.

**`mcp:`** — a server in `.mcp.json` that the Codex config does not declare, or the reverse, or the
same server with a different `command` or different `args` on each side. The remedy line prints the
table to paste. Args matter as much as names: a version pin lives there, so a mirror that agrees on
names and disagrees on args is still drift.

**`portability:`** — either a machine-specific absolute path in a shared config file, or a
directory reference whose capitalisation does not match the real directory. Replace an absolute
path with a repo-relative one, or resolve the root at run time. Fix a mis-capitalised reference to
match the directory exactly — it resolves on a case-insensitive filesystem, so running the command
locally will never catch it. Note that text *about* the mistake is exempted when it quotes the path
with a literal ellipsis, the same exemption the guardrail hook gives a heredoc body.

**`docs:`** — either a missing `AGENTS.md` in `.claude/`, `.codex/` or `.agents/`, which leaves the
sync map with nowhere to live, or a number duplicated into prose that has gone stale against the
assertion count `scripts/check_contrast.py` prints. Update the prose to the current figure, or stop
quoting the figure — a number no gate reads goes stale, and it already did across several files at
once. Do not change the gate to match the prose.

## 3 — the one rule with teeth

**Always repair the mirror. Never weaken the canonical side.** `.claude/` and `.mcp.json` are the
source of truth; `.codex/` and `.agents/` follow them. Deleting a canonical entry, loosening a
threshold in `scripts/check_agents.py`, or granting a subagent a writing tool to silence a check
all turn a reported disagreement into a hidden one. If a check looks wrong, that is a bug in the
check worth fixing in its own change, with the case added — not something to route around here.

`scripts/check_agents.py` belongs to the fixtures and CI stream per `docs/contracts.md`; changing
it is a separate pull request from repairing what it found.

## 4 — verify and report

Re-run `python3 scripts/check_agents.py` until it exits 0. Then report three things:

- **what drifted** — each problem, grouped by prefix, with the file it was in.
- **what you changed** — including anything `--fix` did on your behalf.
- **what you deliberately left alone** — a pre-existing problem in someone else's file, a stale
  number whose owning stream should update it, or anything needing a decision rather than a repair.
  Say why, and name who or what has to resolve it.
