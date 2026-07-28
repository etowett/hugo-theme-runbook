# 002 — Corpus profile: the citizix.com archive

**Status:** measured
**Date measured:** 2026-07-28
**Measured against:** `github.com/etowett/citizix` @ `3b96c36`, Hugo v0.164.0+extended,
hugo-theme-stack v4.0.3
**Supersedes:** the §1 measurements in issue #1, which were taken *before* citizix PR #60

---

## Why this document exists

Runbook's design is derived from a real archive rather than from taste. That only works if the
measurements are current. citizix PR #60 ("Clean legacy WordPress markup from all 497 posts and
disable goldmark unsafe", merged 2026-07-27) rewrote 382 files and materially changed the shape of
the corpus — code block count rose 71%, internal links rose 7×, and the entire WordPress legacy went
to zero.

Every number here was re-measured after that merge with a fence-aware parser. Nothing is inherited
from the original issue.

> **Method note.** Naive `grep` miscounts this corpus badly in both directions: shell `#` comments
> look like Markdown headings, `image:` keys inside Kubernetes YAML look like front matter, and code
> *about* HTML looks like raw HTML. All prose-scoped metrics below exclude fenced code; all
> code-scoped metrics exclude prose. Fence tracking honours CommonMark marker-length rules.

---

## 1. Code is the primary content type

| Metric | Value |
|---|---|
| Posts | 497 (7 drafts, 490 published) |
| Fenced code blocks | **9,046** |
| Mean blocks per post | **18.2** |
| Median / p75 / p90 / p99 | 16 / 23 / 30 / 65 |
| Most in a single post | 158 |
| Posts with no code at all | 6 |
| Inline `` `code` `` spans | **8,049** (16.2 per post) |

## 2. It is overwhelmingly shell

| Language | Blocks | Share |
|---|---|---|
| `sh` | 6,118 | 67.6% |
| `bash` | 1,024 | 11.3% |
| `yaml` + `yml` | 648 | 7.2% |
| `text` | 426 | 4.7% |
| `sql` | 168 | 1.9% |
| `conf` | 162 | 1.8% |
| *(no language tag)* | **93** | 1.0% |
| `tf` + `hcl` | 122 | 1.3% |
| `ini` + `cfg` | 87 | 1.0% |
| `json` | 47 | 0.5% |
| `go` | 34 | 0.4% |
| 36 others | — | — |

**Shell family = 7,143 blocks (79.0%).** 47 distinct languages appear in total.

Design consequence: the syntax palette must be tuned for shell first. Chroma's shell lexer emits a
narrow token set (`nb` builtin, `s`/`s1`/`s2` strings, `c1` comment, `nv` variable, `o` operator) —
those five carry ~80% of all coloured output in this corpus and are the tokens whose contrast
matters most.

## 3. Code blocks are short — the key design constraint

| Length | Exactly | Cumulative | Cum % |
|---|---|---|---|
| **1 line** | **4,090** | 4,090 | **45.2%** |
| 2 lines | 1,065 | 5,155 | **57.0%** |
| 3 lines | 572 | 5,727 | 63.3% |
| 4 lines | 381 | 6,108 | 67.5% |
| 5 lines | 387 | 6,495 | 71.8% |
| 10 lines | 138 | 7,469 | 82.6% |
| > 30 lines | — | 316 | 3.5% |

Median 2 · p75 7 · p90 17 · p99 66 · max **767** lines.

> **The dominant mode is exactly one line, at 45.2% of all blocks** — `sudo dnf -y install redis`.
> A conventional docs-style code block with a full header bar (language label + filename + copy
> button) is *taller than its own content* on nearly half of all blocks. Chrome must scale with
> block size. This single fact drives the adaptive-chrome rule in the design spec.

## 4. Lines are long — horizontal overflow is routine

| Metric | Value |
|---|---|
| Code lines exceeding 80 chars | 4,210 |
| **Blocks containing at least one line > 80 chars** | **1,586 (17.5%)** |
| Longest single line | **854 chars** |

The longest line is a `kubeadm join` with token and CA hash, in
`2021-12-17-how-to-update-upgrade-debian-ubuntu-linux-using-ansible.md`.

The block-level figure (17.5%) is the one that matters for a per-block wrap affordance; the raw line
count overstates the number of places a reader actually encounters overflow. Shell commands are
semantically broken by soft wrapping, so wrapping must never be the default.

## 5. There are effectively no images

| Metric | Value |
|---|---|
| Inline Markdown images across 497 posts | **0** |
| Posts setting an `image:` front-matter field | **1 (0.2%)** |

> The "6 posts" figure in issue #1 was a measurement artifact: 5 of those 6 hits were `image:` keys
> inside **Kubernetes YAML code blocks**, not front matter. Only
> `2021-09-01-install-manjaro-21-gnome-step-by-step-with-screenshots.md` actually sets a cover image.

An image-forward card grid — which is what hugo-theme-stack is built around — optimises for content
that does not exist. Every list view currently reserves space for a cover image that **99.8%** of
posts do not have.

## 6. Prose shape

| Metric | Value |
|---|---|
| Words (excl. code): mean / median | 812 / 722 |
| Words: p75 / p90 / max | 995 / 1,263 / 5,756 |
| Headings | H2 3,250 · H3 2,097 · H4 346 · H5 10 · H6 6 |
| **Body `<h1>`** | **0** |
| Posts with tables | 32 (6.4%) |
| **Internal links per post** | **4.39** (2,183 total) |
| External links | 572 |

Two figures moved sharply from issue #1 and both change design conclusions:

- **Word counts fell** (mean 1,347 → 812). The old figure counted raw `<pre>` code as prose, because
  before PR #60 that code was not inside fences. The corpus is shorter and far more code-dense than
  it appeared.
- **Internal links rose 7×** (0.6 → 4.39 per post), because PR #60 converted 1,607 raw `<a>` anchors
  into Markdown links. The archive now cross-references itself well. Related-posts is therefore a
  *supporting* discovery path, not the primary one — the original justification for promoting it is
  void.

The H2/H3 hierarchy remains flat and consistent (5,347 of 5,709 headings are H2 or H3), so a TOC
keyed to H2–H3 covers 93.7% of headings.

## 7. Taxonomy

> **Re-measured 2026-07-28 (evening).** This section originally described a fragmented taxonomy —
> 49 categories with case-duplicates, 312 tags including typos and malformed entries. The reference
> site has since cleaned it up (citizix#63, #65, #72, #76). Both the original numbers and the
> current ones are kept below, because **the design conclusions were drawn from the messy state and
> most of them still hold** — a theme cannot assume a consumer's taxonomy is clean.

| | When the spec was written | Now |
|---|--:|--:|
| Distinct category strings | 49 | **28** |
| Distinct tag strings | 312 | **302** |
| Tags used exactly once | 159 | **150** |
| Categories holding ≤3 posts | 19 | **4** |
| Malformed tags (spaces, `salt - saltstack`) | 5 | **0** |
| Typo tags (`kubernetees`, `rocky-lonux`) | 5 | **0** |

The build produces **43 category and 308 tag directories** — more than the 28/302 in front matter,
because retired terms now serve redirects from their old URLs.

**What this does not change:** half of all tags are still used exactly once, so a tag cloud remains
the wrong browse affordance, and grouped/counted browse pages are still the right answer. What it
does change is that "the taxonomy is fragmented" is no longer a *citizix* problem — it is a
third-party-robustness assumption, like §9 below.

> Issue #1 §1.7 claims these are "case-duplicates that Hugo treats as distinct terms". **That is
> false.** Verified: `public/categories/` contains one `linux/`, one `aws/`, one `gcp/`, one
> `containers/` and one `security/`. The problem is *display-casing hygiene* — which spelling wins
> the term title is first-seen — not duplicate pages. The design conclusion (grouped browse pages,
> no tag cloud) is unaffected, but the stated reason must be corrected.

**159 tags are used exactly once** (51% of all tags) — a tag cloud is the wrong browse affordance at
this cardinality and distribution.

Case and hyphenation variants in front matter:

| Group | Variants (count) |
|---|---|
| linux | `Linux` (220), `linux` (2) |
| containers | `Containers` (65), `containers` (3) |
| automation | `Automation` (31), `automation` (1) |
| security | `Security` (27), `security` (1) |
| aws | `AWS` (24), `Aws` (1) |
| gcp | `gCP` (6), `GCP` (2), `gcp` (1) |
| almalinux *(tag)* | `alma-linux` (31), `almalinux` (13) |
| archlinux *(tag)* | `arch-linux` (8), `archlinux` (2) |
| cicd *(tag)* | `cicd` (1), `ci-cd` (1) |
| loadbalancer *(tag)* | `load-balancer` (1), `loadbalancer` (1) |

Plus `Uncategorized` (8 posts).

Only **8 posts** carried a minority-spelling category. This was a content fix, not a theme feature —
Runbook should not build normalisation machinery to paper over ten bad strings. It has since been
done in content, which is the right layer.

**But one taxonomy problem *is* the theme's job, and this exercise proved it.** Cleaning the terms
required 83 `_index.md` files, **60 of them existing solely to override a display title** that Hugo
derives badly (`Amazon-Eks`, `Sql-Server`, `Ci-Cd`). That is boilerplate no consumer should have to
write. See [004](004-hugo-mechanics.md) §4a, REQ-TAX-1.

## 7a. Two corpus facts that drive specific features

**Shell prompts are routine, not rare.** **1,389 lines begin with `$ `, across 318 posts (64% of the
archive)**, plus root-`#` prompt blocks. Mixed command-and-output blocks are the norm here.

> Issue #1 §8 Q2 assumes "the citizix corpus mostly omits prompts". **That is false**, and it
> inverts the answer to that question — see
> [006 — Architecture decisions](006-architecture-decisions.md) Q2.

**Terminal box-drawing output is widespread.** **221 posts (44%) contain `└ ├ ─ ●` across 1,177
lines** — `systemctl status` trees, `tree` output, `ss -tulpn` tables. A further 48 posts contain
`→`.

> This is the real constraint on font subsetting, not the 47 languages. A Latin-only subset renders
> these glyphs from the fallback font mid-block, producing mismatched weight and broken box
> alignment. See [003 — Design specification](003-design-spec.md) §3.1.

### Front matter coverage

| Field | Coverage |
|---|---|
| `title`, `description`, `date` | 100% |
| `url` | 99.4% (494) |
| `categories`, `author`, `type` | 99.4% |
| `tags` | 97.6% (485) |
| **`lastmod`** | **90.1% (448)** |
| `keywords` | 28.4% (141) |
| `image` | 0.2% (1) |

`lastmod` was 27.6% before PR #60 stamped 376 posts. The theme can now rely on it being present, but
must still degrade cleanly on the 49 posts without it — never print "Invalid date".

## 8. Post families — the tabs/series question

Titles normalised by replacing distro names and version numbers with placeholders, then grouped.
Families with ≥3 members account for **46 posts (9.3% of the archive)**:

| Family | Posts |
|---|---|
| install and configure Redis «ver» on «distro» | 5 |
| install Java «ver» in «distro» | 4 |
| install and configure MongoDB «ver» on «distro» | 4 |
| install and configure Postgres «ver» on «distro» | 3 + 3 |
| install and set up Jenkins in «distro» | 3 |
| install and configure MariaDB «ver» in «distro» | 3 |
| install RabbitMQ in «distro» | 3 |
| install and set up GitLab CE server on «distro» | 3 |
| install and set up PHP and Nginx (LEMP) on «distro» | 3 |

Real, but issue #1's "the archive is full of install X on Y families" overstates it at 9.3%. Series
and per-distro tabs are worth building for *future* authoring, not for retrofitting 46 posts.

## 9. Legacy WordPress artifacts — cleanup verified complete

| Artifact | Issue #1 | **Measured now** |
|---|---|---|
| Raw `<pre>` in prose | 3,658 tags / 218 posts | **0 / 0** |
| `wp-block-*` classes | 5,342 | **0** |
| `{.wp-block-heading}` attributes | 1,605 | **0** |
| HTML entities inside fences | 256 | **0** |
| Body `<h1>` | 59 posts | **0** |
| Raw `<a href>` anchors | 1,607 | **0** |
| `ocean_*` front matter | 222 | **0** |
| Raw HTML tags in prose | 315 | **0** |
| 4-space indented code blocks | ~355 blocks / 48 posts | **2 blocks / 1 post** |

`&nbsp;`-family entities in prose: **800 across 103 posts**, deliberately retained. Decoding them
breaks CommonMark emphasis flanking (`**bold&nbsp;**` renders bold *because* the entity is literal
text at parse time). citizix PR #60 §4 documents the reasoning.

**Issue #1 §3.4's load-bearing claim — "218 posts (43.9% of the archive) render as unstyled
`<pre>`" — is now 0% and must not survive into the spec in that form.**

### Two survivors — found here, since fixed in content (citizix#62)

> Both were verified against built HTML, fixed in the reference repo, and are recorded here because
> they are the **only remaining empirical basis** for the theme styling bare `pre > code` at all.
> With them gone, that requirement rests entirely on the render-hook behaviour in
> [004](004-hugo-mechanics.md) §1 and on third-party robustness — not on this archive.

1. **`2022-03-03-how-to-install-and-configure-puppet-7-server-on-ubuntu-20-04.md:268`** opens a
   fence with **four** backticks (` ````sh `) and closes at line 270 with **three**. CommonMark
   requires the closing fence to be at least as long as the opening one, so the block never closes:
   **everything from line 269 to end-of-file renders inside a single code block.** On the built page
   the prose "Create new manifest file.", "Paste the following configuration." and "Save and exit."
   all render as code, literal ` ``` ` markers print on the page, and a line-number gutter runs
   52–70+.

   PR #60 missed it because its checker looked for an *odd* count of ` ``` ` markers. This file has
   an even count (56) with a *length* mismatch.

2. **`2021-08-24-how-to-install-and-configure-postgres-13-on-centos-8.md:135`** — the last surviving
   4-space indented block, and the only page in the entire 1,202-page build that emits a bare
   `<pre><code>` with no `.highlight` wrapper.

Both are citizix content defects, not theme defects. They are recorded here because they are the
only remaining empirical basis for the theme styling bare `pre > code` — see
[003 — Design specification](003-design-spec.md) §3.4 for why that requirement survives anyway, on
different grounds.

## 10. URL surface — theme-swap migration risk is low

- All published posts render at root-level `/{slug}/`, driven by front-matter `url:` on 494/497
  posts. Because `url:` lives in content, no theme change can alter post URLs.
- The site *was* configured `permalinks.post: /p/:slug/` while building nothing at `/p/` — inert,
  but armed: any future post written without a `url:` would have landed there, inconsistent with
  every other post. Changed to `/:slug/` in citizix#72 so the default matches the convention.
  **Worth checking in any consumer's config before a theme swap**, since it only misfires on new
  content and so looks harmless right up until it isn't.
- The build reports "355 aliases", but these are **not** legacy redirects. Only **3** come from
  front matter (`aliases:` on the about page). The remaining ~351 are Hugo's automatic
  `/page/1/` → list-root pagination redirects.
- Theme-dependent URLs that Runbook **must** preserve: `/categories/{term}/`, `/tags/{term}/`,
  `/page/{n}/`, `/search/`, and the RSS feed paths.

## 11. Reproducing these measurements

```bash
python3 scripts/profile_corpus.py --dir ../citizix/content/post
```

Stdlib only, no dependencies. It splits front matter on the leading `---` pair, walks the body
tracking fences with CommonMark marker-length semantics (a closing fence must use the same character
and be at least as long as the opener), classifies every line as code or prose, and applies each
metric to the correct partition.

**Run it rather than trusting the numbers above.** They have already gone stale twice in a single
day — once when the reference site's WordPress cleanup landed, which is why this document exists at
all, and again when its taxonomy was consolidated. §7 records both states for exactly that reason.

Which is itself a design finding worth stating plainly:

> The measurements that stayed **stable** across both rewrites are the code-shape ones in §1–§4 —
> block count, blocks per post, shell share, single-line proportion. Those moved by less than 0.1%
> while the taxonomy moved 43%. **Design against the code shape; treat taxonomy and front-matter
> coverage as a snapshot**, because a consumer's will differ and even this one's did not hold still
> for a day.
