# `.codex/` — the Codex CLI mirror

**Claude Code is the source of truth.** `.claude/` and [`.mcp.json`](../.mcp.json) are canonical;
everything in this directory is derived from them. The full reasoning, the authoring gates and the
security note live in [`.claude/AGENTS.md`](../.claude/AGENTS.md); how to actually work on the theme
is the [root `AGENTS.md`](../AGENTS.md).

The point of this directory is that Codex is a first-class client and not a second-rate one: the
same Playwright MCP server, the same `PreToolUse` guardrail, the same skills. What differs is only
the file format each client wants its registrations in.

---

## What is here

| File | What it does |
|---|---|
| `config.toml` | the MCP server set — mirrors `mcpServers` in `.mcp.json` |
| `hooks.json` | the hook registrations — mirrors `hooks` in `.claude/settings.json` |
| `AGENTS.md` | this file |

`.gitignore` re-includes `.codex/agents/` and `.codex/rules/` as well, against the day subagents or
permission rules are mirrored. Neither directory exists yet, and neither does its canonical source
under `.claude/` — do not create one side without the other.

## Sync map

Repeated from [`.claude/AGENTS.md`](../.claude/AGENTS.md) on purpose. The map is cheap and this is
where someone working in Codex will look for it.

| Canonical | Mirror here | Sync |
|---|---|---|
| `.mcp.json` (`mcpServers`) | `config.toml` (`[mcp_servers.*]`) | by hand — `scripts/check_agents.py` compares names, `command` **and** `args` |
| `.claude/settings.json` (`hooks`) | `hooks.json` | by hand — the gate compares which `.claude/hooks/*.py` each side registers |
| `.claude/skills/` | `.agents/skills` symlink | automatic — nothing to do |

Run `python3 scripts/check_agents.py` after changing anything on the left. **The repair direction is
one-way: fix the mirror, never weaken the canonical side.** Removing the Playwright server from
`.mcp.json` silences the gate and takes the capability away from Claude Code too, which is a
regression dressed as a fix.

---

## Hook scripts are shared, never duplicated

`hooks.json` does not contain a hook. It contains a pointer to the one under `.claude/hooks/`:

```
bash -c 'exec python3 "$(git rev-parse --show-toplevel)/.claude/hooks/guardrails.py"'
```

**Why the wrapper rather than a path.** Claude Code substitutes `${CLAUDE_PROJECT_DIR}` into its
own registration in `.claude/settings.json`; a Codex hook command is a plain shell string, and this
repository has nothing that documents an equivalent variable on that side. `git rev-parse
--show-toplevel` resolves the root at run time instead, which keeps the reference **repo-relative**:
it works in a git worktree, in a renamed clone, in a renamed fork and in every other contributor's
checkout, none of which share a prefix.

**An absolute path there was the actual bug.** `check_agents.py` records it in its docstring —
`hooks.json` once hard-coded a path under one contributor's home directory — and
`check_no_absolute_paths` now fails the pull request on any `/Users/.../` or `/home/.../` in the
shared configuration. It is the same rule `.gitignore` already states for `settings.local.json`, in
its own words: committing one "puts one contributor's laptop into everyone's config". It is also
the same failure as the theme's own `--themesDir ../..` trap in the root `AGENTS.md` — a path that
resolves in a default checkout and nowhere else.

**The script itself needs no client-specific handling.** `guardrails.py` reads its payload from
stdin, takes the working directory from that payload, and falls back to `os.getcwd()` when
`CLAUDE_PROJECT_DIR` is unset. Exit 2 blocks the call with stderr shown to the model; exit 0 allows
it. That protocol is what lets one file serve both clients, and it is why a copy under `.codex/`
would be a regression rather than a convenience — the gate reports any `*.py` in a `.codex` hooks
directory as a copy of a shared hook.

## `.gitignore` posture

`.codex/*` is ignored and the shared files are re-included by name, because **Codex writes
per-session state into this directory**. Allow-list what is shared rather than chase what is not —
the inverse of the `settings.local.json` rule and, as `.gitignore` puts it, the same rule applied
the other way round. A new shared file here needs a matching `!` line or it will simply not be
committed, and nobody will notice until the mirror is missing on someone else's machine.

## Getting Codex to load this

`TODO(eutychus): confirm how the Codex CLI discovers project configuration — whether it reads
.codex/config.toml and .codex/hooks.json from the repository root automatically, whether a trust or
approval acknowledgement is needed on first run in a directory, and which command prints the
resolved configuration.` Nothing in this repository establishes any of that, and the file layout
here was ported from another project rather than derived from Codex's own documentation, so a
confident answer would be a guess. Verify against the CLI before writing one in.
