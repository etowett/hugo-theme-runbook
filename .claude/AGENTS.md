# `.claude/` — the source of truth for Runbook's agent configuration

Two clients are wired up in this repository: **Claude Code** (`.claude/`) and the **Codex CLI**
(`.codex/`). This directory and [`.mcp.json`](../.mcp.json) at the repository root are
**canonical**; `.codex/` is a mirror derived from them and `.agents/` holds a symlink. Change the
canonical side first, then propagate.

> Looking for *how to work in this codebase*? That is the [root `AGENTS.md`](../AGENTS.md) — the
> traps, the ownership map, the build recipe, the version floor. Nothing about the theme is
> repeated here. This file answers the other question, *what is available and where does it live*,
> and the tables below are that answer.

The whole tree is gated by [`scripts/check_agents.py`](../scripts/check_agents.py). It exists
because the tooling was copied into this repository and produced two defects within a day, both
recorded in its module docstring: a skill copy under `.agents/` that referred to a hooks directory
under `.Codex` when the directory is `.codex`, and a hook registration in `.codex/hooks.json` that
hard-coded one contributor's home directory. Both are the same shape as the theme's own traps — silent, green, and
wrong in a different checkout — so they get the same treatment as the theme's traps: a gate.

```bash
python3 scripts/check_agents.py          # check only, exit 1 on any problem
python3 scripts/check_agents.py --fix    # repair what is derivable, then check
```

`--fix` repairs only what is mechanically derivable: the `.agents/skills` symlink and a hook
script's executable bit. An MCP server or a hook registration needs judgement and is reported
rather than guessed at, because a script that guesses papers over the disagreement instead of
surfacing it.

It runs in `.github/workflows/ci.yml` on every pull request, so a stale mirror fails the pull
request rather than the next contributor. Run it locally first — it is a few seconds and it tells
you which side to repair.

---

## Sync map

| Canonical source | Mirror | How it is kept in sync |
|---|---|---|
| `.mcp.json` (`mcpServers`) | `.codex/config.toml` (`[mcp_servers.*]`) | by hand — the gate compares the server names, the `command` **and** the `args` |
| `.claude/settings.json` (`hooks`) | `.codex/hooks.json` | by hand — the gate compares which `.claude/hooks/*.py` each side registers |
| `.claude/skills/` | `.agents/skills` symlink | **automatic** — nothing to do; `--fix` recreates the link |
| `.claude/hooks/*.py` | **not mirrored** | the scripts are shared. Only the *registration* differs, because the two clients spell a hook command differently |

`args` are compared and not only names, because **the args list is where a version pin lives**.
`.mcp.json` pins Playwright as `@playwright/mcp@latest`; two mirrors that agree on the name and
disagree on the version are a difference nobody sees until one client reproduces a browser
measurement the other cannot.

**The repair direction is one-way: fix the mirror, never weaken the canonical side.** Every remedy
the gate prints says so. Deleting an MCP server from `.mcp.json` makes the mismatch go away and
takes the capability away from Claude Code as well, which is not a fix.

---

## What lives here

| Path | What it is |
|---|---|
| `settings.json` | Tracked, shared. Hook registration, and today a `permissions.allow` list — see [the allow-list is a public file](#the-permission-allow-list-is-a-public-file) below |
| `settings.local.json` | Per-machine, **gitignored** (`.gitignore` excludes it and `.claude/*.local.json`). Absolute paths and personal overrides belong here and nowhere else |
| `skills/<name>/SKILL.md` | The five shipped skills: `code-block`, `gates`, `hugo-templates`, `new-setting`, `serve`. Read by Claude Code directly and by Codex through `.agents/skills` |
| `hooks/*.py` | `guardrails.py`, the `PreToolUse` guard, and `test_guardrails.py`, its suite. Shared with Codex, **never copied** |
| `agents/*.md` | Subagents: `spec-locator`, `theme-locator`, `contract-reviewer`. All three are `Read, Grep, Glob, Bash` and none of them can write — see the gate below |
| `commands/*.md` | Slash commands: `/agents-doctor`, which runs the gate above |
| `worktrees/` | Scratch git worktrees for parallel sessions, **gitignored**. They are real checkouts of this repository, so committing one nests the tree inside itself |

### Skills, commands and subagents — which one

This is the most common mistake when extending the setup, and the three are not interchangeable.

- **Skill** — a recipe the model finds *on its own*, routed to by its `description`. Use it for
  "when someone wants X, this is the procedure": the render-hook contract, the config ritual.
- **Command** — a deterministic action a human triggers *by name*. No routing, no ambiguity.
- **Subagent** — a separate context window with its own tools and its own system prompt. Use it to
  keep bulky work out of the main conversation.

**If it needs its own context budget → subagent. If the human names it → command. Otherwise →
skill.**

---

## Skill authoring gate

A skill's `description` is loaded in **every session of every client**, whether or not the skill is
ever used — Claude Code reads `.claude/skills/` and Codex reaches the same files through the
`.agents/skills` symlink. One description is therefore a standing context cost carried by everyone
for the whole session.

- **`description` ≤ 400 characters.** That budget is enforced by `check_agents.py`
  (`MAX_SKILL_DESCRIPTION`), and this file is where the gate's error message says the number is
  stated. It is a *routing hint* — when to reach for this — and the procedure belongs in the body.
  Two of the shipped skills are over budget today; the gate names them.
- **`name` must match the directory.** `skills/serve/SKILL.md` declaring `name: dev-server` is a
  skill that cannot be invoked by the path it lives at, and the gate fails on the mismatch.
- **A non-empty body.** A skill that is only frontmatter is a description with nothing behind it.
- **Do not restate the root `AGENTS.md`.** One source of truth per fact — the skills here are thin
  and defer to `docs/` for the reasoning, which is why the traps have not drifted between them.

## Subagent authoring gate

- **`name` must match the filename stem**, the same rule as skills and for the same reason.
- **`description` is required.** Without one nothing can route to it.
- **Read-only tools only.** The gate rejects `Edit`, `Write`, `MultiEdit` and `NotebookEdit` in a
  subagent's `tools`, in its own words: a subagent that can write can bypass the guardrail hook's
  review, because it runs in its own context with its own tool grants. Report findings to the
  caller and let the caller make the edit — then the write goes through the guard like every other
  write.
- **Repo-relative paths only.** A prompt containing `/Users/.../` breaks for every other
  contributor and in every git worktree; `check_no_absolute_paths` fails the pull request on it.
  The exception is deliberate — a line that contains the literal `/Users/...` with an ellipsis is
  exempt, because a document quoting the wrong spelling in order to warn about it is not the
  mistake.

## Hook authoring gate

- **Standard library `python3` only** ([ADR-1](../specs/006-architecture-decisions.md)), matching
  every other script in the repository. There is no package manager here and adding one is a design
  decision, not a convenience.
- **Register it in both clients, pointing at the same file.** `.claude/settings.json` and
  `.codex/hooks.json` must both name the script under `.claude/hooks/`. **Never a copy** — a copy
  of a hook is the exact bug that produced this gate, so `check_agents.py` has a dedicated check
  that reports any `*.py` under `.codex/hooks/` as "a copy of a shared hook", and separately fails
  when a script runs under one client and not the other.
- **An unregistered hook never runs**, and the gate says so: a script on disk that nothing in
  `settings.json` registers is a problem, not a spare part. Test files (`test_*.py`) are exempt.
- **It must be executable.** `--fix` will `chmod +x` it.
- **Resolve the repository root without a client-specific variable.** `guardrails.py` takes `cwd`
  from the hook payload and falls back to `os.getcwd()` when `CLAUDE_PROJECT_DIR` is unset, which
  is what lets one script serve both clients unchanged. See [`.codex/AGENTS.md`](../.codex/AGENTS.md)
  for the wrapper the Codex side needs.
- **Every rule cites the spec that makes it a rule.** If you cannot point at the line in `specs/`
  or `docs/contracts.md` that makes something wrong, it does not belong in the hook — it is policy,
  and policy that nobody agreed to is what teaches people to disable a hook.
- **A false positive is a bug in the hook, not something to work around.** Fix the rule and add the
  case to `test_guardrails.py`. That happened three times while the hook was being written and all
  three are regression cases now.

---

## The permission allow-list is a public file

Runbook is a public repository. `.github/workflows/ci.yml` runs on `pull_request`, so pull requests
arrive from forks, and reviewing one means checking it out locally.

`.claude/settings.json` is **tracked**, and today it carries a `permissions.allow` list that
includes `Bash(hugo *)`, `Bash(python3 scripts/*)` and `Bash(python3 .claude/hooks/*)`. Read those
three as what they are: an instruction to run, with no prompt and no confirmation, commands whose
*behaviour is defined by files in the working tree*. `python3 scripts/anything.py` executes
whatever that branch put in `scripts/`. `hugo` executes whatever `hugo.toml`, `layouts/` and
`exampleSite/` tell it to.

So the risk is not hypothetical and it is not about a malicious maintainer. **Check out a fork's
pull request to review it, open an agent session in that checkout, and the fork has silent code
execution on the reviewer's machine** — approved in advance by a file the fork could not modify but
did not need to, because the allow-list grants the *command shape*, not the *contents*. `gh pr
checkout` is the ordinary review workflow, which is what makes this worth writing down.

The remedy is a three-line change and it is the posture `.gitignore` already assumes elsewhere:

1. Keep only `ask` and `deny` in the tracked `settings.json`. Those are the decisions that should
   be shared, because they are restrictions.
2. Move `permissions.allow` into `.claude/settings.local.json`, which `.gitignore` already
   excludes, so each maintainer opts in on their own machine. `check_agents.py` already skips
   `settings.local.json` by name in its portability check, precisely because that file is where
   machine-specific values are expected to live.
3. Ship a tracked `settings.local.json.example` so the convenience is not lost — copying a template
   is a deliberate act, and pulling a repository is not.

**None of this has been done in this repository.** `settings.json` still tracks the `allow` list
and there is no `settings.local.json.example` in the tree. Whether to make the change is the
maintainer's decision and not an agent's: it trades convenience for a threat model, and the
ownership map assigns `.claude/` to nobody, so it belongs in a pull request of its own rather than
folded into an unrelated change.

`TODO(eutychus): decide whether permissions.allow moves to settings.local.json with a tracked
.example, or stays tracked with the risk accepted in writing.`
