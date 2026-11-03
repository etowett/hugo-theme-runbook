---
title: "A post whose first fence is a diagram"
date: 2026-07-21
description: "The first fenced block here is a text diagram, so this post's card must show no code plate at all."
tags: ["fixtures"]
categories: ["Meta"]
---

```text
┌──────────────┐     OTLP      ┌──────────────┐     gRPC     ┌──────────────┐
│ application  │ ────────────▶ │  collector   │ ───────────▶ │   backend    │
└──────────────┘               └──────────────┘              └──────────────┘
        │                              │
        └──────── traces, logs ────────┘
```

The block above is the point of this page, and it has to be the **first** one.

`list/post-item.html` previews a post's first fence on its card. When that fence is a
`text` block or carries no language at all, it is almost always an ASCII diagram, and
four lines of it cut at 52 characters is cropped box art rather than something a reader
can recognise. So the card for this post has no plate — it starts at its title, the
same as a post with no code.

The shell block below must not be promoted into the card either: previewing a later
fence would show a block out of the context that explains it.

```sh
otelcol --config /etc/otelcol/config.yaml
```
