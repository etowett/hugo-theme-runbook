---
title: "Tables, lists and data"
date: 2026-07-21
description: "The layout fixture: wide tables, nested lists, definition-style prose and footnotes, with almost no code."
tags: ["fixtures", "layout"]
categories: ["Meta"]
series: ["Theme foundations"]
weight: 3
---

32 posts in the reference archive carry a table, and every one of them is a *reference* table —
flags, ports, sizing — read on a phone as often as on a laptop. A table that silently overflows the
viewport is the single most common layout bug in code-first themes, so this page exists to make that
visible at 360 px.

## A table wider than a phone

| Flag | Applies to | Default | Why it matters |
|---|---|---:|---|
| `-n` | `gzip` | off | Suppresses the mtime in the gzip header. Without it byte counts move between runs and every budget gate goes flaky. |
| `-9` | `gzip` | `-6` | Maximum compression. The published budgets are all `-9`, so a `-6` measurement is not comparable. |
| `--panicOnWarning` | `hugo` | off | Promotes warnings to build failures. Hugo demotes missing layouts and broken shortcode arguments to warnings that scroll past in CI. |
| `--printPathWarnings` | `hugo` | off | Reports duplicate target paths, which otherwise silently overwrite one another. |
| `--printUnusedTemplates` | `hugo` | off | Lists templates nothing rendered. Cheap way to catch a layout that stopped being reachable. |
| `--cleanDestinationDir` | `hugo` | off | Removes files no longer produced. Required for any output-diffing gate to mean anything. |

## A narrow table

| Port | Service |
|---:|---|
| 22 | SSH |
| 6379 | Redis |
| 6443 | Kubernetes API |

## A table with alignment and inline code

| Column | Left | Centre | Right |
|---|:---|:---:|---:|
| `redis` | `6379` | running | 1,183 |
| `nginx` | `80`, `443` | running | 991 |
| `kubelet` | `10250` | degraded | 4,204 |

## Nested lists

1. Prepare the host
   - Update the package index
   - Install `redis`
     - From the distribution repository, or
     - From the upstream RPM
2. Configure it
   - Bind to `127.0.0.1`
   - Set `maxmemory-policy`
3. Verify
   - `redis-cli ping` returns `PONG`

## A task list

- [x] Package installed
- [x] Service enabled
- [ ] Backups verified

## Blockquote

> A theme cannot compress content. Page-weight budgets gate the distribution; only theme-shell
> budgets are ceilings.

## Footnote

The archive-smoke layer is a separate concern from these synthetic fixtures.[^layers]

[^layers]: specs/007 §2. Layer 1 lives in this repository and survives content cleanups; Layer 2
    builds the pinned reference corpus and asserts page counts and structural invariants.
