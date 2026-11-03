---
title: "A long post that turns its table of contents off"
date: 2026-07-27
description: "Four headings, enough for a table of contents, and front matter that says not to draw one."
tags: ["fixtures", "toc"]
categories: ["Meta"]
toc: false
---

This page has more headings than `params.runbook.toc.minHeadings` asks for, so on any other page
the table of contents would render. Its front matter carries `toc: false`, the per-page override
`article/toc.html` reads with `isset` rather than `| default`, so there must be no table of
contents here at all — neither the sticky sidebar nor the mobile sheet.

Issue #101 proved the override with scratch pages that were deleted afterwards. This fixture keeps
the proof in the build, so a change that breaks the override shows up as a contents list on this
page.

## Why a page would turn it off

Some posts are long but not navigable: a single narrative that uses headings as pauses rather than
as destinations. A table of contents there is noise, and the author is the only one who knows that.

## Why isset and not a default

`false | default true` is `true`, so the obvious spelling would ignore every author who turned the
feature off. `isset` tells "absent" from "present and false", and the value is compared as text, so
a quoted `"false"` behaves the same as a bare boolean.

## What the check looks for

`check_fixtures.py` guards the source: the front-matter key, and enough headings that the override
is the only reason a contents list could be missing. The built page is checked separately, by
searching its HTML for the table-of-contents class, which should find nothing.

## What it does not cover

The site-wide switch, `params.runbook.toc.enable`, is a different path through the same partial and
is not exercised by this page.
