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

## The shortcodes, now that they exist

The sections above deliberately use GitHub alert syntax rather than shortcodes, because when this
page was written `layouts/shortcodes/` was empty and a call to a shortcode that does not exist is a
hard build failure, not a graceful degradation. Both shortcodes have since landed, so the fixture
picks them up here.

This is not redundancy. CI builds with `--printUnusedTemplates --panicOnWarning`, so a shortcode the
theme ships and no fixture invokes fails the build — which is exactly what it should do. A
capability with no fixture is a capability nobody is testing.

Both invocation forms, because the shortcode accepts either and migrating content should not have to
be rewritten:

{{< admonition type="warning" title="This drops the database" >}}
`DROP DATABASE` is not reversible without a backup. Confirm you have one that restores, not merely
one that exists.
{{< /admonition >}}

{{< admonition tip "The faster way" >}}
`redis-cli --scan --pattern 'session:*'` beats `KEYS` on a live instance.
{{< /admonition >}}

An unknown type degrades to `note` rather than emitting a class no stylesheet knows about — a
silently unstyled warning box is worse than a styled note:

{{< admonition type="nonsense" >}}
Rendered as a note.
{{< /admonition >}}

Collapsible, via native `<details>` and zero JavaScript:

{{< admonition type="caution" title="Long prerequisite list" collapsible="true" open="false" >}}
Collapsed by default, keyboard-operable for free, and still present in find-in-page.
{{< /admonition >}}

## Collapsible output

`details` exists for the `journalctl` dumps and 200-line `terraform plan` output a reader needs to
skip past but that must stay in the DOM, in the page source and in find-in-page. A JavaScript
accordion breaks all three.

{{< details summary="Full systemctl status output" >}}
```text
● redis.service - Redis persistent key-value database
     Loaded: loaded (/usr/lib/systemd/system/redis.service; enabled)
     Active: active (running) since Tue 2026-07-28 09:14:22 UTC; 3h ago
   Main PID: 1183 (redis-server)
     CGroup: /system.slice/redis.service
             └─1183 /usr/bin/redis-server 127.0.0.1:6379
```
{{< /details >}}

The fenced block above is inside the shortcode on purpose: `.Inner` goes through `RenderString`, so
it must still reach the code-block render hook and keep its copy button and its box-drawing glyphs.
