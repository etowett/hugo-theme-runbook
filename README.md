# Runbook

> *A Hugo theme for people who ship procedures, not photographs.*

**Runbook** is a minimal, code-first Hugo theme for technical blogs — sites where the payload is
commands and configuration, not photography.

It is MIT-licensed and built for general use. [citizix.com](https://citizix.com) is its reference
deployment: a 497-post Linux/DevOps archive that every design decision was measured against.

## Status

**Pre-implementation.** The specification is written; the theme is not built yet.

Start with [`specs/README.md`](specs/README.md).

## What makes it different

No widely-used Hugo theme treats the code block as the primary design object. Measured across the
reference archive:

- **9,046 fenced code blocks** across 497 posts — 18.2 per post
- **79% shell** (`sh`, `bash`, `zsh`, `console`)
- **45.2% are exactly one line** — a conventional header bar is taller than its own content
- **17.5% of blocks** contain a line over 80 characters; the longest single line is 854
- **Zero Markdown images**, and exactly one post in 497 sets a cover image

So: chrome that scales with content, horizontal scroll rather than wrapping, a copy button that
works on touch and by keyboard, syntax colours tuned for shell first and contrast-checked token by
token in both light and dark themes — and text-first list views that never reserve space for a cover
image that does not exist.

## Requirements

- Hugo **v0.146.0 or later**, extended not required
- No Node, no npm, no build toolchain

## Licence

[MIT](LICENSE).
