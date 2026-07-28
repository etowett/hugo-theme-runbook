# Runbook — specification

> *A Hugo theme for people who ship procedures, not photographs.*

Runbook is a minimal, code-first Hugo theme for technical blogs — sites where the payload is commands
and configuration, not photography. It is MIT-licensed and intended for general use; **citizix.com**
is its reference deployment and the archive every design decision here was measured against.

## Read in this order

| Doc | Contents |
|---|---|
| [001 — Overview](001-overview.md) | Scope, audience, non-goals, success criteria |
| [002 — Corpus profile](002-corpus-profile.md) | Measured profile of the 497-post reference archive |
| [003 — Design specification](003-design-spec.md) | Typography, colour, the code block, layouts, a11y, SEO |
| [004 — Hugo mechanics](004-hugo-mechanics.md) | Verified Hugo behaviour the theme depends on |
| [005 — Performance budgets](005-performance-budgets.md) | Budgets and how they are measured |
| [006 — Architecture decisions](006-architecture-decisions.md) | ADR-0 … ADR-9 and resolved open questions |
| [007 — Verification](007-verification.md) | Test and verification plan |
| [008 — Milestones](008-milestones.md) | Delivery plan, M0 … M6 |
| [009 — Showcase compliance](009-showcase-compliance.md) | Hugo Themes submission requirements |
| [010 — citizix migration](010-citizix-migration.md) | Migration and cutover for the reference deployment |

## The five decisions that matter most

1. **The code block is the product.** 9,046 fenced blocks across 497 posts — 18.2 per post, 79%
   shell, **45.2% exactly one line**. Chrome must never exceed content height, so no block gets a
   header bar unless it has something to put in it.
   ([003](003-design-spec.md) REQ-CB-2)

2. **The hook must never trust site config.** `transform.Highlight` inside a render hook inherits the
   *consumer's* `markup.highlight` settings, and Hugo merges theme config underneath site config. The
   reference site sets `lineNos: true` today — that is what puts a line-number gutter on a one-line
   command across 484 pages. A theme default cannot fix it; the hook must force its own options.
   ([004](004-hugo-mechanics.md) §2, [003](003-design-spec.md) REQ-CB-1)

3. **Page weight is not a theme budget.** Only 22 of 493 articles (4.5%) are under 7 KB gzipped
   today, with a median of 10,663 B. A theme cannot compress content. Budget the **theme shell**
   against synthetic fixtures, and gate the **archive distribution** at p50/p90 with a
   no-regression rule.
   ([005](005-performance-budgets.md))

4. **No required images.** Zero Markdown images across the whole archive; exactly one post sets a
   cover image. Text-first lists, cover images as an optional capability.
   ([006](006-architecture-decisions.md) ADR-7)

5. **Extension points, not template forking.** The reference site carries ten local override files
   today. Without documented hooks for head markup, analytics and comments, every consumer forks
   templates and every update becomes a merge conflict.
   ([006](006-architecture-decisions.md) ADR-8)

## Status

Greenfield. No implementation exists yet; this directory is the specification that precedes it.

These documents supersede the original proposal in
[issue #1](https://github.com/etowett/hugo-theme-runbook/issues/1), which was written before citizix
PR #60 removed the entire WordPress legacy from the reference archive and reshaped the corpus. All
measurements were re-taken on **2026-07-28** against the post-merge content, and two independent
technical reviews of the original proposal are folded in. Where sources conflicted, the conflict was
resolved by measurement or by checking a primary source, and the resolution is recorded inline.
