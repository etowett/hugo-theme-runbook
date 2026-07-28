# Design tokens

**Status:** stub — owned by the design-system workstream.

The token **names** are frozen ([contracts §2.1](contracts.md#21-css-custom-properties)); the values
live in [`assets/css/tokens.css`](../assets/css/tokens.css) and are what this workstream owns.

## To document

- The full `--rb-*` inventory: name, purpose, and which pairs are contrast-critical
- The accent hue and both palette definitions — this closes **open decision #1** in
  [006](../specs/006-architecture-decisions.md#decisions-still-open)
- Is the bundled font on or off by default — **open decision #2**
- The Chroma palette method: which tokens were tuned, against which backgrounds, and the measured
  ratios. Shell first — `nb`, `s`/`s1`/`s2`, `c1`, `nv`, `o` carry roughly 80% of all coloured
  output in the reference corpus, and comments are the token most themes fail
- Font subset provenance: source, the tool, the exact Unicode ranges, resulting byte size, and the
  licence. JetBrains Mono is OFL-1.1 with **no Reserved Font Name**, so a subset may keep the name
- Which tokens consumers may override, and which are internal
