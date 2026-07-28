# Code blocks

**Status:** stub — owned by the code-block workstream.

The differentiating feature. Requirements are [003 §3.3](../specs/003-design-spec.md) REQ-CB-1 …
REQ-CB-8; verified Hugo behaviour is [contracts §3](contracts.md#3-verified-hugo-behaviour).

## Author-facing attributes

Hugo's canonical lowercase names, so this documentation matches upstream examples.

| Attribute | Effect |
|---|---|
| ` ```bash {linenos=true} ` | Line numbers for this block only |
| ` ```bash {hl_lines="2-4"} ` | Highlight lines |
| ` ```yaml {file="docker-compose.yml"} ` | Filename label — this is what triggers the header bar |
| ` ```console {prompt="$"} ` | Prompt-aware copy |
| ` ```text {output=true} ` | Command-output treatment |

## To document

- Why no block has a header bar by default, and what makes one appear (REQ-CB-2). 45.2% of blocks
  in the reference corpus are exactly one line and 57.0% are two or fewer — a header bar taller than
  its own content is the majority case, not the exception
- Copy semantics: exactly what is copied and what is not (REQ-CB-4)
- **Why `$ ` is never stripped heuristically.** 1,389 lines across 318 posts begin with it, mixed
  command-and-output blocks are routine, `#` may be a real shell comment and `$` may be data. Use
  `{prompt="$"}` to opt in per block; it is never inferred from content
- Wrap toggle: session-local, never persisted, and why. Wrapping is a property of the one long line
  being inspected, not a reading preference — persisting it silently re-breaks the next command the
  reader copies by eye
- The `output` treatment and its interaction with `guessSyntax: true`, which speculatively colours
  untagged output — precisely what the treatment exists to avoid
- Line numbers are opt-in per block and **cannot** be turned on site-wide (REQ-CB-1)
- Indented code has no copy button, no language tag and no wrap toggle, and cannot have them: it
  bypasses the render hook in every Hugo version
- The `.wp-block-code` snippet for WordPress-migrated sites — documented here, not shipped as bytes
