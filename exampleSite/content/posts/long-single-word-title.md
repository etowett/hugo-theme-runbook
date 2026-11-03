---
title: "Internationalisation"
date: 2026-07-24
description: "A one-word title wider than a phone, so the heading has to break the word rather than pan the page sideways."
tags: ["fixtures", "layout"]
categories: ["Meta"]
---

The title of this page is a single word of twenty letters. At the article h1 size in the display
face it is wider than a 390 px viewport, and a heading that refuses to break a word widens the whole
document — the reader then pans sideways on every line of prose, not just the title. The reference
archive hit exactly this with "Infrastructure" on its home page (issue #67).

## Kubernetesadministration

The heading above is the same failure one level down: a compound with no break opportunity, at the
h2 size. Both must wrap inside the measure, and `document.documentElement.scrollWidth` must equal
`clientWidth` at 390 px.
