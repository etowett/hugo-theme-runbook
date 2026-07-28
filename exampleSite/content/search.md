---
title: "Search"
layout: "search"
description: "Client-side search over a metadata-only index — the fixture for layouts/search.html and layouts/search.json."
outputs:
  - html
  - json
# No `menu` entry on purpose: header.html already renders the search link itself,
# gated on params.runbook.search.enable, so adding one here would produce two.
---

Runbook indexes **metadata only**: the title, the summary, the date and the taxonomy terms.
Post bodies are not indexed and **code is never indexed** — not fenced blocks, not inline
spans, not the filename or language chrome around them.

That is a deliberate limit rather than an unfinished feature. Indexing the full text of this
theme's reference archive produces a 4.55 MB file (1.2 MB gzipped) that every visitor to
`/search/` downloads before they can type; the metadata index for the same 490 posts is about
180 KB, 40 KB gzipped. Getting the full-text version under budget needs a build-time index
compiler from npm, and [ADR-1](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md)
rules out requiring a Node toolchain to build a blog.

So search here finds posts by **what they are about**, and the post itself is where you read
the commands. If you know a phrase is in a specific post, your browser's find-in-page on the
[archive](/archive/) is the better tool.

`docs/search.md` covers the index schema, the byte budget, the cache policy, and how to turn
this on for your own site.
