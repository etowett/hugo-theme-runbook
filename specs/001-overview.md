# 001 — Runbook: overview, scope and non-goals

**Status:** approved direction, specification in progress
**Last revised:** 2026-07-28

> *A Hugo theme for people who ship procedures, not photographs.*

---

## 1. What Runbook is

Runbook is a minimal, code-first Hugo theme for technical blogs — sites where the payload is
commands and configuration, not photography.

It has **two audiences**, and both are first-class:

1. **citizix.com** — the reference deployment. A 497-post Linux/DevOps archive currently running
   `hugo-theme-stack`. Runbook replaces it.
2. **Third-party technical blogs** — Runbook is open source under MIT and published to
   [themes.gohugo.io](https://themes.gohugo.io) so anyone can use it.

The reference deployment exists to keep the design honest: every design decision in these specs is
derived from measuring a real archive rather than from taste. But citizix is the *test case*, not
the *customer*. Where a decision would serve citizix at the expense of general adoption, general
adoption wins, and the spec says so explicitly.

## 2. Scope

**In scope**

- A complete Hugo theme: layouts for home, single, list, taxonomy, term, archive and 404.
- A best-in-class code block — the differentiating feature (§4).
- Light and dark themes, both meeting WCAG 2.2 AA, with a no-flash toggle.
- Text-first list views with no assumed cover images.
- Sticky table of contents, related posts, series support, client-side search.
- Content shortcodes: admonition, tabs, details, filetree.
- Documented extension points so consumers can inject analytics, comments and custom head markup
  without forking templates.
- Publication to the Hugo Themes showcase.

**Out of scope**

- **euxven.com.** Earlier drafts of this project stated Runbook would power euxven.com. It will not.
  euxven.com is a marketing and landing page, not a blog, and its needs have nothing in common with
  a code-first blog theme. All references have been removed, including from the rollout sequence.
- Bundled comment providers. Runbook ships an extension point and documentation, never a vendor.
  See [006](006-architecture-decisions.md) Q5.
- Bundled analytics or advertising. Site-owner concerns, wired through extension points.
- A CMS, an admin UI, or content migration tooling.
- Full-text client-side search. See [005](005-performance-budgets.md) §4 — the index size makes it
  untenable without an npm post-build step, which [006](006-architecture-decisions.md) ADR-1 rejects.

## 3. Why a new theme

The reference archive was profiled in full ([002 — Corpus profile](002-corpus-profile.md)). Three
measured facts make existing general-purpose themes a poor fit:

1. **9,046 fenced code blocks across 497 posts — 18.2 per post, 79% shell.** Code is not an accent
   in this content; it is the content.
2. **45.2% of code blocks are a single line.** Conventional docs-style code chrome (a full header
   bar with language label, filename and copy button) is taller than its own content on nearly half
   of all blocks.
3. **Zero Markdown images; one post in 497 sets a cover image.** The image-forward card grid that
   `hugo-theme-stack` is built around optimises for content that does not exist. Every list view
   currently reserves space for a cover image 99.8% of posts do not have.

No widely-used Hugo theme treats the code block as the primary design object. That is the gap
Runbook fills.

## 4. The differentiator

**The code block.** Everything else in the theme is competent-and-conventional; the code block is
where Runbook earns its existence. Specifically:

- Chrome that scales with content, so a one-line `sudo dnf -y install redis` is not dwarfed by its
  own header bar.
- Horizontal scroll rather than wrapping by default, because soft-wrapping a 854-character
  `kubeadm join` silently changes what the reader thinks the command is.
- A copy button that copies exactly the code, works on touch, and is keyboard reachable.
- Syntax colours tuned for shell first, with every Chroma token contrast-checked in both themes.

Full requirements in [003 — Design specification](003-design-spec.md) §3.

## 5. Success criteria

Runbook is done when all of the following hold:

| # | Criterion |
|---|---|
| 1 | citizix.com runs on Runbook in production with verified URL, RSS, sitemap and canonical parity against the Stack build |
| 2 | Accepted into the Hugo Themes showcase, with a demo that builds against latest Hugo |
| 3 | Theme-shell budgets met: CSS ≤ 8 KB gz, core article JS ≤ 3 KB gz, ≤ 2 script tags, zero theme-added third-party hosts |
| 4 | Page-weight distribution gates met against the real archive (see [005](005-performance-budgets.md) §3.2) |
| 5 | Both themes pass automated WCAG 2.2 AA contrast over prose **and every Chroma token** |
| 6 | Every page readable and navigable with JavaScript disabled |
| 7 | A consumer can add analytics, comments and custom head markup without editing a theme template |

## 6. Document map

| Doc | Contents |
|---|---|
| 001 (this) | Scope, audience, non-goals, success criteria |
| [002](002-corpus-profile.md) | Measured profile of the reference archive |
| [003](003-design-spec.md) | Design specification — typography, colour, code block, layouts, a11y, SEO |
| [004](004-hugo-mechanics.md) | Verified Hugo behaviour the theme depends on |
| [005](005-performance-budgets.md) | Performance budgets and how they are measured |
| [006](006-architecture-decisions.md) | ADRs and resolved open questions |
| [007](007-verification.md) | Test and verification plan |
| [008](008-milestones.md) | Delivery milestones |
| [009](009-showcase-compliance.md) | Hugo Themes showcase requirements |
| [010](010-citizix-migration.md) | Migration and cutover plan for the reference deployment |

## 7. Provenance

This specification supersedes the original proposal in
[etowett/hugo-theme-runbook#1](https://github.com/etowett/hugo-theme-runbook/issues/1).

The original proposal was written before citizix PR #60 ("Clean legacy WordPress markup from all 497
posts and disable goldmark unsafe"), which rewrote 382 content files. That merge invalidated a large
part of the proposal's evidence base: code-block count rose 71%, internal links rose 7×, and the
entire WordPress legacy — which the proposal named as its "non-negotiable" differentiator — went to
zero. Every measurement in these specs was re-taken on 2026-07-28 against the post-merge archive.

The revised specification incorporates two independent technical reviews of the original proposal.
Where the reviews disagreed with each other or with the original, the disagreement was resolved by
measurement or by checking a primary source; those resolutions are recorded inline.
