---
name: hugo-templates
description: How Hugo's post-v0.146.0 template system works in this theme and which constructs break one end of the supported version range. Use before adding or renaming anything under layouts/, when a template is not being reached, when a build warns about a deprecation, or when deciding where a new template file belongs.
allowed-tools: Read Grep Glob Bash(hugo *) Bash(python3 *)
---

# Templates

Runbook targets Hugo's **post-v0.146.0 template system only** and ships no legacy layout tree
([ADR-0](../../../specs/006-architecture-decisions.md)). That is why `min_version = "0.146.0"` in
`theme.toml` is a hard floor rather than a suggestion: `layouts/_partials/`, `layouts/_markup/`,
`page.html` and `home.html` do not resolve below it.

## Where things go

| Kind | Path | Was, before v0.146.0 |
|---|---|---|
| Page kinds | `layouts/page.html`, `home.html`, `list.html`, `section.html`, `taxonomy.html`, `term.html`, `404.html` | `layouts/_default/single.html`, `index.html`, `_default/list.html` … |
| Partials | `layouts/_partials/**` | `layouts/partials/**` |
| Render hooks | `layouts/_markup/render-{codeblock,link,image,heading}.html` | `layouts/_default/_markup/**` |
| Shortcodes | `layouts/shortcodes/**` | unchanged in this repository |
| Output formats | `layouts/rss.xml`, `layouts/search.json` | |

**Never add `layouts/_default/`.** When a legacy path exists beside the new one the legacy one
wins, *silently* — the modern template you just edited stops having any effect and nothing warns.
The guardrail hook blocks writes to `layouts/_default/` and `layouts/partials/`.

> `TODO(agents): confirm.` Hugo's v0.146.0 overview also renames `layouts/shortcodes` to
> `layouts/_shortcodes`. This repository ships `layouts/shortcodes/`, and it builds clean under
> `--panicOnWarning` on both ends of the CI matrix — so the old spelling is still resolved, not
> merely tolerated. Whether to move is a decision for the ADR-0 owner, not something to change in
> passing; the hook deliberately does **not** block `layouts/shortcodes/`.

## The version range cuts both ways

CI builds **0.146.0 non-extended** and **latest**, because both ends break independently, and
`--panicOnWarning` turns a deprecation warning into a failure.

Hugo v0.158.0 deprecated `languageCode`, `.Language.LanguageCode` and
`.Language.LanguageDirection`. Their replacements — `locale`, `.Locale`, `.Direction` — **do not
exist at the 0.146.0 floor**, so either side of that pair breaks one end of the matrix.

```go-html-template
{{ site.Language.Lang }}                              {{/* stable across the whole range */}}
{{ site.Language.Params.direction | default "ltr" }}  {{/* RTL is a language param */}}
```

```toml
[languages.ar.params]
  direction = "rtl"
```

Runbook also omits `languageCode` from its own configs for the same reason.

**Extended is not required.** ADR-0 declares it, CI builds the floor non-extended to prove it, and
a template feature that quietly needs extended has broken the theme's own manifest. That rules out
`resources.ToCSS` / SCSS.

## Every template needs a fixture or a written reason

`--printUnusedTemplates` under `--panicOnWarning` would mean deleting every fallback the demo site
does not exercise, which for a theme published for general use means deleting the code that exists
for consumers unlike the demo. So `scripts/check_unused_templates.py` still fails by default, but
accepts an entry in `.github/unused-templates-allowed.txt` **carrying a reason** — and a waiver
that has gone stale fails too, so a template going dead later cannot hide behind one.

It has already caught four templates shipping with nothing reaching them: `render-image.html`,
`admonition.html`, `details.html` and `archive.html`. Add the fixture in `exampleSite/content/`
**with** the feature.

## House rules for template code

- `partialCached` for anything whose answer cannot vary per page. Settings are read exactly once:
  `{{- $rb := partialCached "utils/settings.html" . -}}` — see `/new-setting`.
- Every user-visible string comes from `i18n/en.yaml`, appended **inside your own section**.
- CSS custom properties are `--rb-` prefixed and declared in `assets/css/tokens.css`. The load
  order in `head/css.html` is the cascade contract — `tokens → base → layout → code →
  chroma-light → chroma-dark → print` — and **nobody edits that list**. `resources.Get` skips a
  stylesheet that does not exist, so a new empty one is harmless.
- Three theme states on `<html data-theme>`: `auto`, `light`, `dark`. **CSS must already be
  correct for all three before JavaScript runs**; `head/theme-guard.html` only ever changes the
  answer. Storage key `runbook:theme:v1`, every access in `try`/`catch`.
- JSON-LD is **assembled as a map and `jsonify`d once**, then marked `safeJS`. Go's
  `html/template` re-escapes `jsonify` output inside a `<script>` block, so interpolating it
  emits double-encoded values and dates that are not valid ISO 8601. It still *parses*, so review
  does not catch it — the reference site shipped it on **493 of 493** article pages.
  `scripts/check_jsonld.py` asserts on parsed values for that reason: `headline` must not begin
  with a quote character, `datePublished` must match `^\d{4}-\d{2}-\d{2}T`.

## Diagnosing

```bash
hugo --source exampleSite --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination public --cleanDestinationDir --panicOnWarning --printPathWarnings \
     --templateMetrics --templateMetricsHints
```

`--printPathWarnings` catches two pages resolving to the same target path, where one silently
overwrites the other. `--templateMetrics` is for when a build gets slow; it is not part of any
gate.
