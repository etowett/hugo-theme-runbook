# Configuration reference

**Status:** stub — owned by the templates workstream. The complete annotated reference is an M5
deliverable ([008](../specs/008-milestones.md)); it starts here at M1 so it is never a retrofit.

Every Runbook setting lives under **`params.runbook`**. Nothing is read from a bare top-level param,
so the theme cannot collide with a consumer's own keys or with another theme's. See
[contracts §2.4](contracts.md#24-configuration).

The authoritative defaults are the `[params.runbook]` block in the repo-root
[`hugo.toml`](../hugo.toml), which Hugo merges *underneath* a consuming site's own configuration.

## Required of the consuming site

```toml
[markup.highlight]
  noClasses = false   # ADR-2 — inline Chroma styles make dual-theme highlighting impossible
```

Line-number settings need no attention: the render hook forces its own
([REQ-CB-1](../specs/004-hugo-mechanics.md#2-transformhighlight-inside-the-hook-inherits-the-consumers-site-config)),
so `lineNos = true` in a site config does nothing to Runbook.

To use the `series` taxonomy, register it — a theme cannot register a taxonomy:

```toml
[taxonomies]
  series = "series"
```

## To document

- Every `params.runbook.*` key: type, default, effect, and the milestone it arrived in
- Front-matter schema, matching `archetypes/default.md`
- Per-page overrides and their precedence against site config
- Migration mapping from `hugo-theme-stack` (`image`, `toc: false`)
- The `params.runbook.taxonomyTitles` acronym map (REQ-TAX-1)
- `params.runbook.cspNonce` and the published inline-guard hash (ADR-4)
