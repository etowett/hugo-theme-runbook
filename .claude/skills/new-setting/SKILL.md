---
name: new-setting
description: Add a configuration setting to the theme correctly — the params.runbook namespace, the isset dance for booleans that default to true, the two defaults, the i18n string and the documentation entry. Use whenever a change introduces something a consuming site should be able to turn on, off or configure, or when a value is about to be hard-coded into a template.
argument-hint: "[setting name]"
allowed-tools: Read Grep Glob Edit Bash(hugo *) Bash(python3 *)
---

# Adding a configuration setting

A setting that exists only in a template is a setting nobody can discover. Five steps, and it is
not done until all five are.

## 0 — should it be a setting at all?

The theme ships **no analytics, no ads, no comment vendor and no live IDs**. If the answer is
"the consumer supplies a snippet", it is not a setting — it is one of the six ADR-8 extension
points in `layouts/_partials/hooks/`, which are empty on purpose and stay that way. Read
[docs/extending.md](../../../docs/extending.md) before adding a param.

## 1 — namespace it

**`params.runbook.*`**, always ([contracts §2.4](../../../docs/contracts.md)). Nothing is read
from a bare top-level param, ever, so Runbook can never collide with a consuming site's keys.
The three exceptions already in the tree — `mainSections`, `description`, `author` — are Hugo's
own site-level conventions, not Runbook keys, and the list does not grow.

The guardrail hook blocks a new `site.Params.<anything-else>`.

## 2 — resolve it in one place

Every read goes through [`layouts/_partials/utils/settings.html`](../../../layouts/_partials/utils/settings.html),
called as `{{- $rb := partialCached "utils/settings.html" . -}}`. No template reads
`site.Params.runbook` directly.

That rule has already been broken once and it cost a real bug: `head/theme-guard.html` bypassed
the partial, emitted hard-coded colours, and — being first in `<head>` — beat the configurable
pair `seo.html` emitted, so `params.runbook.themeColor` was silently ignored. **A "single place
configuration is read" with one exception is not a single place.**

### Booleans whose default is `true`

```go-html-template
{{- $showLastmod := true -}}{{ if isset $rb "showlastmod" }}{{ $showLastmod = $rb.showLastmod }}{{ end }}
```

Not `| default true`. `false | default true` evaluates to `true`, so the obvious spelling
silently ignores every consumer who turns the feature off. `isset` distinguishes "absent" from
"present and false".

**The probe string is lower-case on purpose:** `isset` is case-sensitive and Hugo lower-cases
every param key, so `isset $rb "showLastmod"` is always false.

Booleans whose default is `false`, and non-booleans, may use `| default`.

### Values that must stay real booleans

`head/theme-guard.html` tests `eq … false`, so anything it reads has to come out of the partial
as a boolean rather than a string. `bundledCodeFont` and `codeFontLigatures` are the existing
cases.

### Values that need validating, not passing through

`themeMode` is checked against `slice "auto" "light" "dark"` and falls back to `auto`. An
unrecognised value used to fall through to the media-scoped branch — right by accident for
`"system"`, silently wrong for anyone who typed it meaning something else. If a setting has a
fixed set of legal values, validate it here.

## 3 — default it twice

1. the root [`hugo.toml`](../../../hugo.toml) — what the theme ships;
2. inline in `utils/settings.html` — so the theme still behaves when a consumer's config omits
   the block entirely, and so keys added after the root config was frozen have a home.

The two must agree. A mismatch is a bug that only shows up on a site that did not copy the
example config.

## 4 — every user-visible string comes from i18n

`i18n/en.yaml`, **inside your own section** — the file is sectioned so parallel workstreams do
not collide. No exceptions: a hard-coded string cannot be translated, and retrofitting means
touching every layout.

## 5 — document it

[`docs/configuration.md`](../../../docs/configuration.md) belongs to the release-hygiene stream.
If it is not yours to edit: record the setting in your own doc and **list it in the pull-request
body**, so its owner can fold it into the reference. Do not edit across the ownership boundary.

## Then

Add or extend a fixture in `exampleSite/content/` that exercises the new path — add it *with* the
feature, not afterwards — and run `/gates`. A shipped template that no fixture reaches fails CI.
