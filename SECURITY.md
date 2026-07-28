# Security policy

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Report privately through GitHub Security Advisories:

<https://github.com/etowett/hugo-theme-runbook/security/advisories/new>

> **Maintainer note.** Private vulnerability reporting is **not yet enabled** on this repository —
> the API reported it disabled on 2026-07-28, so the link above returns 404 until it is switched on
> in *Settings → Advanced Security*.
> `TODO(eutychus): enable private vulnerability reporting.` Until then, open a public issue
> containing **only** "requesting a private channel for a security report" and no details, and a
> private advisory will be opened for you.

A useful report contains: the theme version or commit, the Hugo version, the affected file or
template, a minimal reproduction (ideally a `content/` file plus the relevant `hugo.toml` fragment),
and what an attacker gains. A scanner finding with no reproduction may well be a false positive.

**What to expect.** Acknowledgement within 5 working days; an assessment within 10; a fix or a
written decision not to fix, with reasons, in the advisory. Credit in the advisory and the changelog
unless you ask otherwise. There is no bounty.

## Supported versions

| Version | Supported |
|---|---|
| `main` | Yes — the only thing that exists |
| tagged releases | None yet |

From the first release, the latest release is supported and older majors get security fixes only for
six months after the next major is tagged. See
[CHANGELOG.md](CHANGELOG.md#versioning-upgrades-and-deprecation).

---

## Threat model

Runbook is a **static Hugo theme**. It has no server, no database, no authentication, no forms and no
user accounts. It executes at two moments: at **build time** inside Hugo on your machine or your CI
runner, and at **render time** in a reader's browser from the HTML it produced.

**Markdown content is trusted input.** Runbook assumes the person writing the content is the person
running the build — which is true of essentially every Hugo blog. If your site renders Markdown
submitted by other people, read [URL handling](#2-url-handling) carefully first; that assumption
stops being safe and the theme does not defend it for you.

What Runbook deliberately does not do, which removes most of the usual surface:

- **No third-party requests.** No analytics, no ads, no comment provider, no font CDN, no icon
  library, no live vendor ID anywhere in the theme or in `exampleSite`. `check_showcase.py` fails the
  build if a tracking credential appears in `exampleSite`.
- **No network at runtime** except your own origin (and only when search is enabled).
- **One inline script** — the ~160-byte theme guard — and it is hashable or nonce-able.
- **Subresource integrity** on the fingerprinted CSS and JavaScript bundles in production builds.
- **Storage** is one key, `runbook:theme:v1`, every access wrapped in `try`/`catch`, and the value is
  validated against `light|dark|auto` before it is stamped on the document — a poisoned storage value
  cannot inject an attribute.

---

## The surfaces that actually matter

### 1. Code-block metadata

Fence attributes — `{file="…"}`, `{caption="…"}`, `{prompt="$"}` — are author-supplied strings that
end up in element text and in a `data-` attribute. **This is escaped correctly.** Verified against a
build of `main`:

````markdown
```sh {file="<img src=x onerror=alert(1)>" caption="<b>c</b>" prompt="<script>"}
echo hi
```
````

renders as `&lt;img src=x onerror=alert(1)&gt;`, `&lt;b&gt;c&lt;/b&gt;` and
`data-rb-prompt="&lt;script&gt;"`. Go's `html/template` contextual autoescaping does this, and the
render hook does **not** reach for `safeHTML` on any attribute value.

The one `safeHTML` in the hook is applied to the output of `transform.Highlight` — Chroma's own
generated markup, over content Chroma itself escaped — and it is unavoidable, because the alternative
is printing the highlighted HTML as visible text. The hook's string manipulation of that output is
two literal `replace` calls that strip `tabindex="0"`; neither introduces content.

**If you change the render hook:** never move author input into a `safeHTML`, `safeHTMLAttr` or
`safeJS` context, and never stash the code text in a `data-` attribute. The copy handler reads
`textContent` from the DOM precisely so that it does not have to.

### 2. URL handling

Link and image destinations from Markdown are emitted through `| safeURL`, which **bypasses Go's URL
sanitiser**. Verified against a build of `main`: `[click](javascript:alert(1))` produces
`<a href="javascript:alert(1)">`, and the same holds for an image destination. Without `safeURL` Go
would have rewritten it to `#ZgotmplZ`.

This is the standard spelling for a Hugo link render hook and it is what makes `mailto:`, `tel:` and
protocol-relative URLs work, so it is not a defect on its own. It **is** the precise reason the trust
boundary above matters:

> **If your site publishes Markdown you did not write, sanitise it before Hugo sees it.** Runbook
> will faithfully render a `javascript:` link.

Mitigations already in place for ordinary sites:

- `markup.goldmark.renderer.unsafe = false` in the shipped configuration, so raw HTML in Markdown is
  dropped rather than rendered. CI additionally builds with `unsafe = true` forced on, to prove the
  theme still builds under a consumer's hostile configuration — not to endorse it.
- External links get `rel="noopener noreferrer"`, and `target="_blank"` is off by default.
- A Content Security Policy with `script-src 'self'` plus a nonce or hash blocks a `javascript:`
  navigation outright. **Ship one** — see
  [configuration § Content Security Policy](docs/configuration.md#content-security-policy).

### 3. SVG handling

- **The theme's own icons are inert.** Copy, copied and wrap are `data:image/svg+xml` **`mask-image`
  URLs inside CSS**, not inline SVG in the document. A masked image cannot execute script, cannot
  reference an external resource, and never enters the DOM. Under CSP they need `img-src … data:`.
- **The image render hook excludes SVG from measurement.** Hugo classifies SVG as an image resource,
  but `.Width` requires decoding it and asking is a build error, so no `width`/`height` is emitted for
  an SVG. That is a correctness decision, not a security control.
- **Your own SVGs are your responsibility.** An SVG placed in `static/` and referenced with
  `<img src>` cannot execute script — browsers do not run script in an image context — but the same
  file navigated to directly, or embedded through `<object>`/`<iframe>`, **can**. Runbook never
  inlines an SVG from content, and with `unsafe = false` it cannot. If you enable `unsafe = true` and
  paste SVG into Markdown, you own what is in it.

### 4. Search-result escaping

**Not built yet.** Client-side search is M4b and had not landed when this file was written; when it
does, this section will describe what it actually does rather than what it should.

The requirement it must meet, stated now so it is not discovered later: a search result is
**untrusted-shaped output** even on a fully trusted site, because it is content re-serialised into a
JSON index and then re-inserted into the DOM by JavaScript, which is a context where Go's contextual
autoescaping no longer protects anything.

- Build result markup with `textContent` and `document.createElement`, **never** with `innerHTML`.
- If matches are highlighted, do it by wrapping split text nodes, not by string-substituting into
  HTML.
- The index is generated by a Hugo template, so escape at generation with `jsonify`, and treat the
  index as data at consumption — never `eval`, never `new Function`, never inject it into a
  `<script>` block.
- The index is **metadata-only** (title, summary, tags), which also keeps it small.

### 5. Front matter and JSON-LD

Front-matter values reach `<meta>` content, Open Graph tags and JSON-LD. JSON-LD is emitted by
`jsonify`-ing a whole map and passing it through `safeJS`, so Go escapes the values as JSON and the
`<script type="application/ld+json">` block is a data island the browser never executes. Per-field
interpolation into that block is the pattern that goes wrong; do not introduce it. `check_jsonld.py`
asserts every block parses and that specific field values are well-formed.

### 6. Build-time and supply chain

- **No dependency manifest at all.** No `package.json`, no `go.mod`, no `requirements.txt`, no lock
  file. The only things that execute at build time are Hugo itself and Python scripts in this
  repository, and those import nothing outside the standard library.
- **GitHub Actions are the one dependency surface**, and Dependabot is configured for them.
- **Do not add a vendored binary or a `curl | sh` step**, in CI or in the documentation.
- **Nothing in this repository should ever contain a credential.** Secret scanning and push
  protection are on. `exampleSite` is additionally checked for tracking IDs by
  `scripts/check_showcase.py`.
- Hugo Modules is an offered install path and it fetches code over the network at build time. That is
  one of the reasons it is not the recommended path
  ([ADR-9](specs/006-architecture-decisions.md)).

### 7. What you add through the hooks

The six override hooks are unrestricted by design — they exist so you can add analytics or comments
without forking a template. Anything you put in `custom-head.html`, `custom-body-end.html` or
`comments.html` runs with full page privileges, will need CSP allowances, and is outside this policy.
The theme ships zero vendors specifically so that adding one is a decision you make explicitly.

---

## Out of scope

- Vulnerabilities in Hugo, Chroma, Go, or GitHub Actions — report those upstream.
- Anything requiring the attacker to already control your `content/`, your `hugo.toml`, or your build
  pipeline. If they have that, they can write anything they like into the output.
- Missing security headers on **your** host. Runbook cannot set an HTTP header; it can only be
  compatible with a strict policy, which it is.
- Automated scanner output with no reproduction.
- Denial of service by building an enormous site.
