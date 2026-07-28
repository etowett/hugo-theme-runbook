---
name: serve
description: Start the Hugo development server for exampleSite with the theme-path spelling that works in a git worktree, a renamed clone and a renamed fork. Use when asked to run, preview, serve or look at the demo site, or when a change needs checking in a browser rather than in the markup.
argument-hint: "[port]"
allowed-tools: Bash(hugo *) Bash(lsof *) Read
---

# Dev server

```bash
hugo server --source exampleSite \
            --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
            --disableFastRender --panicOnWarning \
            --port ${1:-1313}
```

Run it in the background and report the URL. Three flags, three reasons:

- **`--themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")"`** — `exampleSite/hugo.toml`
  declares `theme = "hugo-theme-runbook"`, so Hugo looks for a *directory of that name* inside
  `--themesDir`. `--themesDir ../..` resolves only because a plain checkout happens to sit in a
  directory with the repository's name; in a worktree it fails with
  `module "hugo-theme-runbook" not found`. This pairing needs no symlink and no edit to
  `exampleSite/hugo.toml`, which belongs to another workstream.
- **`--disableFastRender`** — fast render skips work that the render hooks and the JSON search
  index depend on, so a partial rebuild can show you output the real build never produces.
- **`--panicOnWarning`** — otherwise the server logs a missing layout or a bad shortcode call at
  WARN and keeps serving, and you debug the symptom instead of reading the cause.

## Checking a change in the browser

Two of the code block's real bugs — `padding-inline-end` not counting toward scrollable overflow,
and a `<td>` growing so its inner `<pre>` never gets a width to scroll against — were **invisible
in the markup** and were found by driving a browser. If a change touches overflow, focus order,
the copy button, the wrap toggle, the theme toggle or the table of contents, look at it. The
`.mcp.json` in this repository wires up Playwright for that.

Pages worth loading, all under `exampleSite/content/`:

| Path | What it exercises |
|---|---|
| `/posts/code-block-smoke-test/` | every code-block attribute combination |
| `/posts/code-blocks-158/` | 158 blocks on one page — chrome cost at scale |
| `/posts/code-block-767-lines/` | one very long block; overflow and `tabindex` |
| `/posts/tables-and-data/` | the `<td>`-width bug's regression case |
| `/posts/rtl-bidirectional-text/` | direction handling |
| `/posts/tabs-and-variant-procedures/` | the tabs shortcode, which ships **no JavaScript** |
| `/search/` | the lazy search chunk and its separate 3 KB budget |

Check both themes. The toggle is in the header; the three states on `<html data-theme>` are
`auto`, `light` and `dark`, and **CSS must already be correct for all three before JavaScript
runs** — the guard only ever changes the answer. If something looks right only after the toggle
is clicked, that is the bug, not the fix.

## Do not

Do not point the server at the reference archive, and do not commit anything from
`exampleSite/public/` — it is gitignored, and the built demo is not a review artefact.
