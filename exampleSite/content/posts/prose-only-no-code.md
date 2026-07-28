---
title: "Why page-weight ceilings do not work"
date: 2026-07-23
description: "A post with no code block at all — the case a code-first theme is most likely to get wrong."
tags: ["fixtures", "budgets"]
categories: ["Meta"]
---

Six posts in the 497-post reference archive contain no code at all, and they are the pages a
code-first theme is most likely to render badly. Everything tuned for a dense procedure — tight
leading, a narrow measure chosen so an 80-column block fits, a table of contents assuming
`##` headings every few hundred words — has to still work when the payload is paragraphs. There is
no code block anywhere on this page, deliberately, and there are no headings for the first several
hundred words either, so the table of contents has to cope with starting late.

The original budget proposal asked for article HTML at or below 7 KB gzipped, enforced in CI.
Measured across the 493 pages whose structured data declared themselves articles, compressed with
`gzip -n -9`, the median was 10,663 bytes and the ninetieth percentile 15,488. Twenty-two pages —
four and a half per cent of the archive — were at or below seven kilobytes. A gate written that way
would have failed ninety-five per cent of the archive before the new theme contributed a single
byte, and it would have failed them for having content.

The mistake is a category error rather than a calibration error. Total page weight is dominated by
what the author wrote. A post with five thousand seven hundred words of prose and a seven-hundred
line configuration listing cannot be compressed into a fixed ceiling by any theme, because the
bytes are the post. A theme can only be held responsible for the bytes it adds: its stylesheet, its
script, its markup scaffolding, the structured data it emits. Those are worth a hard ceiling,
because a regression in them is unambiguously the theme's fault.

## What replaced it

So the budgets split in two. Theme-shell budgets are hard ceilings and are read off a synthetic
fixture page with fixed minimal content, so the figure reflects only theme output. Page-weight
budgets gate the shape of the distribution instead: a median, a ninetieth percentile, and a rule
that no individual page may get heavier than the same page rendered by the theme being replaced.
That last rule is the one that actually protects readers, and it is the only one of the three that
survives the archive changing underneath it.

There is a second lesson hiding in the numbers, which is that the obvious culprit was the wrong one.
Removing every line-number table from a sampled article saved 109 gzipped bytes. Removing one field
from its structured data — a duplicate of the entire article text, emitted a second time as
`articleBody` — saved 432. The line numbers were still worth removing, for reasons that have nothing
to do with bytes, but the claim that syntax-highlighting markup dominated the page was simply not
true, and it was believed for a long time because nobody had measured it.

## Why the baselines expire

Both of the distribution gates were written against a measurement taken before the reference site
fixed its structured data and turned off site-wide line numbers. Those two changes alone moved the
median from 10,663 bytes to 9,159 and the ninetieth percentile from 15,488 to 11,626. The proposed
median gate of nine thousand bytes was set as a fifteen per cent improvement; it is now within one
per cent of what the old theme already achieves, so passing it demonstrates nothing.

A no-regression gate is only meaningful against a baseline captured at the same commit as the thing
being compared. Copying a number out of a document that was accurate three weeks ago produces a gate
that looks rigorous in the configuration file and measures nothing in practice, which is worse than
having no gate, because it consumes the attention that a real gate would have earned.
