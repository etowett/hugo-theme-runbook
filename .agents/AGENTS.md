# `.agents/` — shared between agent clients

This directory holds **no configuration**. It holds one thing: a tracked symlink,
`skills -> ../.claude/skills`, so that more than one client can reach Runbook's skills without a
second copy of them existing.

## Why a symlink and not a copy

Because the copy that used to live here had drifted **within a day** of being made. Its version of
the `gates` skill referred to a hooks directory under `.Codex` when the directory is `.codex` — a
find-and-replace artefact of a byte copy. That resolves on a case-insensitive macOS filesystem and
fails on the Linux CI runner, so it could not be caught by running the command locally and would
have shipped green.

`scripts/check_agents.py` now carries a check for exactly that shape: any reference to a
dot-directory that differs from the real one only in case is a failure, in all three tooling
directories. And `check_skills_symlink` fails if this path is a directory of copies, points
somewhere other than `../.claude/skills`, or is missing; `--fix` recreates the link when nothing is
in the way.

The general rule the two checks encode: **one source of truth per fact.** A skill edited under
`.claude/skills/` is immediately correct everywhere, because there is nowhere else for it to be
wrong.

`TODO(eutychus): confirm which clients actually scan .agents/skills.` The symlink is maintained on
the assumption that Codex reads skills from here, and nothing in this repository verifies that.

## Where configuration lives instead

| Client | Configuration |
|---|---|
| Claude Code | [`.claude/`](../.claude/AGENTS.md) — **canonical**, and where the authoring gates are written down |
| Codex CLI | [`.codex/`](../.codex/AGENTS.md) — a mirror of the above |
| any client | [`.mcp.json`](../.mcp.json) at the repository root — the MCP server set |

## Adding another client

1. Give it its own top-level directory.
2. Point its skills at `.agents/skills` if it supports a skills directory. Do not copy them.
3. Mirror `.mcp.json` and `.claude/settings.json` into whatever format it wants — never the other
   way round. `.claude/` stays canonical, and a mirror that has grown its own settings is no longer
   a mirror.
4. Teach `scripts/check_agents.py` to check the new mirror in the same change, so it cannot
   silently rot. `.codex/` is the worked example: its two files are compared field by field, not
   merely counted.
