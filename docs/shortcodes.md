# Shortcodes and content components

Runbook ships **three** shortcodes and **one** content component that is not a shortcode.

| Thing | Where | Needs JavaScript |
|---|---|---|
| [`admonition`](#admonition) | `layouts/shortcodes/admonition.html` | no |
| [`details`](#details) | `layouts/shortcodes/details.html` | no |
| [`tabs`](#tabs) / `tab` | `layouts/shortcodes/tabs.html`, `tab.html` | no |
| [`filetree`](#filetree--deliberately-not-shipped) | **not shipped** — see below | — |
| [Series navigation](#series-navigation) | `layouts/_partials/article/series.html` | no |

Every visual rule for the three shortcodes lives in `assets/css/components.css`. There is no
per-shortcode stylesheet and no injected `<style>` block: the reference site's admonition CSS is
injected per page ([010 §3](../specs/010-citizix-migration.md)), which means a reader on one of the
496 posts that use no admonition still pays for it. Runbook's version is 245 B gzipped in
the one budgeted stylesheet, shared by every page and cached once.

## Scope, honestly

The reference archive of 497 posts uses `admonition` in **exactly one** post, and uses `tabs`,
`details` and `filetree` **zero** times ([003 §3.5](../specs/003-design-spec.md)). These exist for
future authoring, not to retrofit an archive. That fact set the bar for everything below: a
shortcode that would have cost the theme meaningful bytes, JavaScript or accessibility debt did not
get built.

---

## `admonition`

Note, tip, important, warning, caution, danger.

```text
{{< admonition type="warning" title="Data loss" >}}
This drops the database. `DROP DATABASE` is not reversible without a backup.
{{< /admonition >}}
```

Positional arguments work too, so content migrating from another theme does not have to be
rewritten:

```text
{{< admonition tip "The faster way" >}}...{{< /admonition >}}
```

| Parameter | Positional | Default | Effect |
|---|---|---|---|
| `type` | 0 | `note` | `note` · `tip` · `important` · `warning` · `caution` · `danger` |
| `title` | 1 | the translated type name | Heading text |
| `collapsible` | — | `false` | `true` renders a native `<details>` — zero JavaScript |
| `open` | — | `true` | `false` collapses it. Only meaningful with `collapsible` |

An unknown `type` degrades to `note`. It does **not** pass the value through into a class name: a
silently unstyled warning box is worse than a correctly styled note.

**Colour is never the only signal.** `tokens.css` declares no status colours and
`components.css` may not invent one — a colour that is not a token is a colour
`scripts/check_contrast.py` never gates, and shipping an unverified foreground/background pair is
what [003 §3.2](../specs/003-design-spec.md) exists to prevent. So the type name itself is the
signal: a real, translated word in the DOM, which survives greyscale printing, deuteranopia and a
screen reader. On top of that, one tier of reinforcement — `warning`, `caution` and `danger` take an
amber inline-start rule, reusing `--rb-code-hl-border` because it is already asserted at 3:1 against
this exact background in both palettes.

Each type also gets a `rb-admonition--<type>` class and a `data-rb-admonition` attribute. Those are
the hook if you want six distinct colours on your own site — add them in your own stylesheet via the
[`custom-head` hook](extending.md), and contrast-check them.

## `details`

Collapsible long output. Native `<details>`, zero JavaScript.

````text
{{< details summary="Full systemctl status output" >}}
```text
● redis.service - Redis persistent key-value database
     Loaded: loaded (/usr/lib/systemd/system/redis.service; enabled)
```
{{< /details >}}
````

| Parameter | Positional | Default | Effect |
|---|---|---|---|
| `summary` | 0 | the translated "Details" | The closed-state label |
| `open` | — | `false` | `true` renders it expanded |

This is sized for what the corpus actually holds: `journalctl` dumps and 200-line `terraform plan`
output that a reader needs to skip past but that must stay in the DOM, in view source and in
find-in-page. A JavaScript accordion breaks all three. `<details>` breaks none of them and is
keyboard-operable for free.

Fenced code inside it goes through `RenderString` in block display, so it still reaches
`layouts/_markup/render-codeblock.html` and keeps its language tag, copy button and wrap toggle.

## `tabs`

One procedure, one panel per variant — `apt` / `dnf` / `zypper`.

````text
{{< tabs title="Install nginx" >}}
{{< tab name="apt" >}}
```sh
sudo apt install -y nginx
```
{{< /tab >}}
{{< tab name="dnf" >}}
```sh
sudo dnf install -y nginx
```
{{< /tab >}}
{{< /tabs >}}
````

`tabs`:

| Parameter | Default | Effect |
|---|---|---|
| `title` | — | Visible label for the group; also names the jump strip |
| `level` | `3` | Heading level for the panel titles, 2–6 |
| `id` | slug of `title`, else the shortcode's ordinal | Anchor prefix |

`tab`:

| Parameter | Positional | Default | Effect |
|---|---|---|---|
| `name` | 0 | translated `Option N` | Panel label — the heading and the strip link text |
| `id` | — | slug of `name` | Anchor slug, if the label should not decide the URL |

A `tab` outside a `tabs` block is a build error, not a silent no-op. The alternative is content that
exists in your Markdown and nowhere in the built page, which is the failure this family exists to
prevent.

Set `id` explicitly if you intend to link to a panel from elsewhere. Without a `title` the prefix
falls back to the shortcode's ordinal on the page, and that moves the moment someone inserts a
paragraph above it. Panel anchors are `#rb-<block id>-<tab slug>`.

Set `level` when the default would skip a heading level. A shortcode cannot see what heading it is
nested under, and [003 §3.6](../specs/003-design-spec.md) requires correct heading order. These
headings do **not** appear in Hugo's table of contents — `.TableOfContents` is built from Markdown
headings only, so a tabs block never floods the TOC rail with distro names.

### Nothing is hidden, and that is the design

There is no tab strip that switches panels. Every panel renders, stacked, each under a real heading,
with a strip of same-page links above them.

[ADR-5](../specs/006-architecture-decisions.md) states the requirement rather than a preference:
tabs expose **all** panels without JavaScript. `assets/js/runbook.js` is frozen at three modules and
tabs are not one of them, so the only *switching* mechanisms available are CSS-only ones — the
radio/checkbox pattern, `:target`, or `:has()`. All three were evaluated and rejected. Each puts
`display: none` on the panels the reader did not pick, and that costs four things:

1. **Find-in-page.** <kbd>Ctrl</kbd>+<kbd>F</kbd> for `zypper` finds nothing on the page that
   documents `zypper`. For a reference whose whole job is "the reader finds the command", that is a
   correctness bug, not a degraded experience.
2. **Print and PDF.** `assets/css/print.css` exists because these procedures get printed
   ([005 §4](../specs/005-performance-budgets.md)). A switched strip puts one panel on paper and
   drops the rest silently.
3. **The search index.** `layouts/index.json` is built from the page's text, so a hit can land a
   reader on a page where the matching words are invisible until they guess which control reveals
   them.
4. **Honest semantics.** `role="tab"` belongs on something focusable that the browser exposes as a
   tab. A `<label>` is not focusable; putting the role on the `<input type="radio">` instead is a
   role conflict that ARIA in HTML forbids. What is left announces as a radio group, and the panel
   swap is never announced at all — announcing it requires the script that does not exist.

Stacked panels have none of those failure modes and need no ARIA state, no roving `tabindex` and no
live region, because there is no state to represent. Keyboard operation is whatever the browser does
with a link, which is the correct answer; following one also moves the sequential-focus starting
point into the panel, so the next <kbd>Tab</kbd> continues from the content the reader jumped to.
`:target` puts an accent rule on the panel you landed on — it marks where you are, it never decides
what is visible.

Verified with scripting disabled at the browser's content-setting level, not merely by reading the
markup: every panel's commands render, and the copy buttons are still `hidden` in that run, which is
the positive control proving no script executed.

If a future baseline offers a switching mechanism that keeps all four properties above, it can be
swapped in behind these class names without touching a single page of content. That is the other
reason this is a shortcode and not a Markdown convention.

## `filetree` — deliberately not shipped

`filetree` is listed in [003 §3.5](../specs/003-design-spec.md). It was evaluated and **declined**.
Write the tree as a fenced block:

````text
```text
etc/nginx/
├── conf.d/
│   └── default.conf
├── nginx.conf
└── sites-enabled/
    └── example.com -> ../sites-available/example.com
```
````

Four reasons, in order of weight:

1. **The capability already exists and is already guaranteed.** `└ ├ ─ │` are in the bundled
   monospace subset by explicit requirement — REQ-FONT-1 exists because 221 posts, 44% of the
   archive, draw box-drawing glyphs inside code and a fallback face substituting mid-block breaks
   column alignment. A fenced block therefore renders a tree correctly *by design*, not by luck.
2. **A generated `<ul>` would be worse for the reader.** The block above is what `tree` printed and
   what the reader's copy button hands back — paste-able into a terminal or a ticket. A nested list
   re-drawn with CSS pseudo-element connectors cannot be copied as `tree` output, and it loses the
   copy button, the language tag and the wrap toggle that every code block already has.
3. **The bytes are not free.** The connectors, the indent guides and their RTL handling are a real
   stylesheet cost inside a theme-wide 8,000 B gzipped budget that also has to hold search.
4. **Zero demand.** The reference archive uses it zero times in 497 posts. [003
   §3.5](../specs/003-design-spec.md) is explicit that these are affordances for future authoring
   and must not block the core theme; spending budget on the one with no user and a working
   alternative is the wrong trade.

If a consuming site wants a semantic tree, `layouts/shortcodes/` in the site overrides the theme's —
nothing here has to be forked to add one.

---

## Series navigation

Not a shortcode. `layouts/_partials/article/series.html` renders it automatically from a taxonomy,
and `layouts/page.html` already calls it.

### It does not work until you register the taxonomy

**A theme cannot register a taxonomy.** Hugo replaces `[taxonomies]` wholesale rather than merging
it, so the moment a consuming site declares any taxonomy of its own, anything the theme declared is
gone. [003 §3.4](../specs/003-design-spec.md) is explicit that series therefore ships *with
documentation or it does not work*. This is that documentation.

In your site config:

```toml
[taxonomies]
  tag = "tags"
  category = "categories"
  series = "series"
```

Listing `tag` and `category` is not optional here. Declaring only `series` replaces Hugo's defaults
and your tag and category pages disappear.

Then in each post's front matter:

```yaml
---
title: "Running Redis on Ubuntu 24.04 — part 1: install"
series: ["Redis on Ubuntu"]
---
```

Until the taxonomy is registered, `utils/terms.html` returns nothing and the partial renders
nothing: no error, no warning, no half-working navigation.

### What it renders

A `<nav>` with the series title linking to the term page, a "Part *n* of *m*" line, and an ordered
list of every post in the series. The current post is a `<span aria-current="true">`, not a link to
itself.

It renders **only when the series has more than one post**. A "Part 1 of 1" box is noise.

### Order

**Chronological ascending unless you say otherwise.** Hugo's default page order is date-descending,
which is right for an archive and backwards for a series — part 1 is the oldest post.

To set an explicit order, put `weight` in front matter. The partial switches to `ByWeight` if *any*
post in the series carries one, so a partially weighted series behaves predictably instead of
silently reverting to dates.

### Settings

| Key | Type | Default | Effect |
|---|---|---|---|
| `params.runbook.seriesTaxonomy` | string | `"series"` | Which registered taxonomy drives this. Change it if yours is called something else |

---

## Adding a string

Every user-visible string comes from `i18n/en.yaml` — no exceptions
([contracts §2.5](contracts.md#25-strings)). The shortcode keys live under `# ── Shortcodes ──`:

| Key | Used by |
|---|---|
| `admonitionNote` … `admonitionDanger` | Default `admonition` titles |
| `detailsSummary` | Default `details` label |
| `tabsVariants` | Accessible name of the jump strip when a `tabs` block has no `title` |
| `tabsUnnamed` | Fallback panel label when a `tab` has no `name` |

There is deliberately no "selected tab" or "tab *n* of *m*" string. Nothing is hidden, so there is no
state to announce and nothing that would need translating into a state announcement.

## Fixtures

`exampleSite/content/posts/admonitions-and-callouts.md` covers `admonition` and `details`;
`exampleSite/content/posts/tabs-and-variant-procedures.md` covers `tabs`, `tab` and the fenced-block
file tree. Both are required, not decorative: CI runs `hugo --printUnusedTemplates` against
`.github/unused-templates-allowed.txt`, so a shortcode no fixture invokes fails the build. A
capability with no fixture is a capability nobody is testing.
