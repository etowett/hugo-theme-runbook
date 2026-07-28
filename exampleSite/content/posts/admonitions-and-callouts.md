---
title: "Admonitions and callouts"
date: 2026-07-22
description: "GitHub-style alert blockquotes, plus the plain blockquotes they must not break."
tags: ["fixtures", "layout"]
categories: ["Meta"]
---

Procedures need warnings, and a runbook theme that renders "do not run this on production" as
ordinary prose has failed at its one job.

These are written as **GitHub alert blockquotes**, not as shortcodes, on purpose:

- A shortcode call is a hard build failure when the shortcode does not exist, and
  `layouts/shortcodes/` is owned by the templates workstream and still empty. This page has to build
  today.
- Alert syntax degrades to a plain blockquote with a visible `[!NOTE]` marker, which is ugly but
  never fatal — so the fixture lands ahead of the render hook and the day
  `layouts/_markup/render-blockquote.html` arrives, the visual diff shows exactly what changed.
- It is also what a third-party author will actually write, having copied it from GitHub.

## Alerts

> [!NOTE]
> Useful information a reader can skip without consequence.

> [!TIP]
> A shortcut. `redis-cli --scan --pattern 'session:*'` beats `KEYS` on a live instance.

> [!IMPORTANT]
> Line numbers are opt-in per block. A consuming site setting `lineNos = true` must not put a
> gutter on this theme's blocks — REQ-CB-1.

> [!WARNING]
> `--cleanDestinationDir` deletes files in the destination that the build no longer produces. Point
> it at the wrong directory once and you will find out what was in there.

> [!CAUTION]
> Never run the archive smoke build against a destination that also serves production.

## A plain blockquote, which must still look like a quote

> A perfect automated accessibility score is not WCAG conformance. It is a perfect automated
> accessibility score.

## A blockquote containing a code block

> Reproduce every published measurement with:
>
> ```sh
> hugo --gc --minify --destination public
> gzip -n -9 -c public/index.html | wc -c
> ```
>
> The `-n` is not optional.

## A nested blockquote

> The original plan proposed validating against the reference archive with seven fixed fixture
> pages.
>
> > Three of those seven pages no longer exist.

## An alert next to a code block

> [!WARNING]
> This restarts the service. Connections in flight are dropped.

```sh
sudo systemctl restart redis
```
