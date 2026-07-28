# Extending Runbook without forking it

Runbook ships six stable, empty, documented override partials
([ADR-8](../specs/006-architecture-decisions.md#adr-8--documented-extension-points-not-template-forking)).
Copy the path into your own site's `layouts/` and Hugo uses yours instead.

| Override this | Rendered |
|---|---|
| `layouts/_partials/hooks/custom-head.html` | last in `<head>` — analytics, verification tags, extra CSS |
| `layouts/_partials/hooks/custom-body-start.html` | first inside `<body>` — e.g. a GTM `<noscript>` |
| `layouts/_partials/hooks/custom-body-end.html` | last before `</body>` — deferred third-party scripts |
| `layouts/_partials/hooks/comments.html` | foot of a single page |
| `layouts/_partials/hooks/article-footer.html` | after the article, before related and comments |
| `layouts/_partials/hooks/custom-schema.html` | in `<head>`, after the theme's own JSON-LD |

**Why this exists.** The reference deployment carries ten local override files today. Without
documented hooks, every consumer forks templates and every theme update becomes a merge conflict.

**The theme ships no vendors.** No analytics, no ads, no comment provider, no live IDs. Nothing
loads until your site opts in, which is what keeps theme JavaScript at zero for these features.

---

## Comments

Runbook ships **zero comment providers and one hook**
([Q5](../specs/006-architecture-decisions.md#q5--comments--ship-zero-providers-ship-one-hook)).
Both of the snippets below are complete: create the file, set the IDs, done.

Disqus is documented alongside giscus **deliberately**. The reference deployment runs Disqus with
years of existing threads, and a giscus-only theme would force it to choose between losing that
history and hacking the theme — which would invalidate the theme's own migration story.

### giscus

```go-html-template
{{/* layouts/_partials/hooks/comments.html */}}
{{ if and .IsPage (not .Params.disableComments) }}
<section class="rb-comments" aria-label="Comments">
  <script src="https://giscus.app/client.js"
          data-repo="{{ site.Params.giscus.repo }}"
          data-repo-id="{{ site.Params.giscus.repoId }}"
          data-category="{{ site.Params.giscus.category }}"
          data-category-id="{{ site.Params.giscus.categoryId }}"
          data-mapping="pathname"
          data-strict="1"
          data-reactions-enabled="1"
          data-emit-metadata="0"
          data-input-position="top"
          data-theme="preferred_color_scheme"
          data-lang="{{ site.Language.Lang }}"
          crossorigin="anonymous"
          async></script>
  <noscript>Comments require JavaScript.</noscript>
</section>
{{ end }}
```

```toml
[params.giscus]
  repo = "you/your-repo"
  repoId = "R_..."
  category = "Announcements"
  categoryId = "DIC_..."
```

`data-theme="preferred_color_scheme"` follows the system, which is right for Runbook's `auto` mode
but does **not** follow an explicit light/dark choice from the theme toggle. If you need it to,
post a `setConfig` message to the giscus iframe from your own script — that is site code, not theme
code, and it belongs in `custom-body-end.html`.

### Disqus

```go-html-template
{{/* layouts/_partials/hooks/comments.html */}}
{{ if and .IsPage site.Config.Services.Disqus.Shortname (not .Params.disableComments) }}
<section class="rb-comments" aria-label="Comments">
  <div id="disqus_thread"></div>
  <script>
    var disqus_config = function () {
      this.page.url = {{ .Permalink }};
      this.page.identifier = {{ .Permalink }};
    };
    (function () {
      var d = document, s = d.createElement('script');
      s.src = 'https://{{ site.Config.Services.Disqus.Shortname }}.disqus.com/embed.js';
      s.setAttribute('data-timestamp', +new Date());
      (d.head || d.body).appendChild(s);
    })();
  </script>
  <noscript>Comments require JavaScript.</noscript>
</section>
{{ end }}
```

```toml
[services.disqus]
  shortname = "your-shortname"
```

**Thread continuity when migrating.** Disqus keys threads on `disqus_identifier`, falling back to
the URL. If your previous theme let Disqus default to the page URL — as the reference deployment's
did — keep `this.page.identifier` set to the same `.Permalink` and existing threads survive the
theme change. Change it and every thread on the site orphans silently.

---

## Analytics, tag managers and ads

IDs stay in **your** site config. The theme never sees them and never ships them.

### GA4 — `custom-head.html`

```go-html-template
{{ if and hugo.IsProduction site.Params.ga4 }}
<script async src="https://www.googletagmanager.com/gtag/js?id={{ site.Params.ga4 }}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', {{ site.Params.ga4 }});
</script>
{{ end }}
```

### GTM — `custom-head.html` plus `custom-body-start.html`

The container script goes in `custom-head.html`; the `<noscript>` iframe **must** be the first
thing inside `<body>`, which is exactly what `custom-body-start.html` is for. The reference site
currently carries this as a forked theme template — the merge-conflict trap this hook removes.

```go-html-template
{{/* layouts/_partials/hooks/custom-body-start.html */}}
{{ with site.Params.gtm }}
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={{ . }}"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
{{ end }}
```

### AdSense — `custom-head.html`

```go-html-template
{{ with site.Params.adsenseClient }}
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ . }}"
        crossorigin="anonymous"></script>
{{ end }}
```

> The Hugo Themes showcase forbids third-party tracking with live credentials in `exampleSite`
> ([009 §2](../specs/009-showcase-compliance.md)). Put these in your own site, never in the demo.

---

## Extra structured data

`custom-schema.html` renders inside `<head>`, after the theme's own JSON-LD.

### REQ-SEO-1 applies here too

Go's `html/template` contextually autoescapes the body of a `<script>` block as JavaScript and
**re-escapes JSON that is already valid**. This is not a hypothetical: it shipped on **493 of 493**
article pages of the reference site for months, because the broken output still parses.

```go-html-template
{{/* WRONG — emits "name":"\"Example Ltd\"" */}}
<script type="application/ld+json">
{ "@type": "Organization", "name": {{ site.Title | jsonify }} }
</script>
```

```go-html-template
{{/* RIGHT — build a map, jsonify ONCE, mark it safeJS */}}
{{ $org := dict
  "@context" "https://schema.org"
  "@type" "Organization"
  "name" site.Title
  "url" site.Home.Permalink
  "sameAs" (slice "https://github.com/you" "https://fosstodon.org/@you")
}}
<script type="application/ld+json">{{ $org | jsonify | safeJS }}</script>
```

One `jsonify` per `<script>`. A second one inside the same block is the bug.
See [004 §2a](../specs/004-hugo-mechanics.md).

---

## Restyling

**Override custom properties; do not fork a stylesheet.** A forked stylesheet is a merge conflict
on every theme update; a custom property override is three lines that keep working.

```go-html-template
{{/* layouts/_partials/hooks/custom-head.html */}}
<style>
  :root { --rb-accent: #0b6bcb; }
  :root[data-theme="dark"] { --rb-accent: #7cc4ff; }
</style>
```

The token list is in `assets/css/tokens.css` and documented in
[design-tokens.md](design-tokens.md). Read it before inventing a token name — the `--rb-*` names
are a frozen shared contract between workstreams (contracts §2.1).

If you must add real CSS, add a stylesheet through `custom-head.html` rather than editing the
theme's. It loads last and wins.

---

## Behaviour contracts a consumer can rely on

These attributes and classes are part of the public surface. They will not be renamed without a
major version.

| Hook | Meaning |
|---|---|
| `<html data-theme>` | `auto` / `light` / `dark`; storage key `runbook:theme:v1` |
| `[data-rb-theme-toggle]` | The theme toggle button. Ships `hidden`; JavaScript unhides it |
| `[data-rb-toc]` | The table-of-contents `<nav>` that scroll-spy observes |
| `.rb-toc-link[aria-current="true"]` | The TOC entry for the heading currently being read |
| `.rb-link-external` | An outbound link. The indicator is a CSS pseudo-element |
| `.rb-heading-anchor` | The permalink beside a heading. **Must stay focusable** — reveal it on `:hover` and `:focus-visible`, never `display: none` |

## Overriding a template

Anything under `layouts/` can be overridden by putting a file at the same path in your own site.
Prefer, in order:

1. a `params.runbook.*` setting;
2. a hook partial;
3. a small partial override (`_partials/article/meta.html` is a common one);
4. a whole template — last resort, because it is the thing you now maintain.

`layouts/_markup/render-*.html` overrides are a legitimate customisation point, but note that
Runbook ships the code-block hook **only** at `layouts/_markup/render-codeblock.html`. Do not create
`layouts/_default/_markup/render-codeblock.html`: the legacy path takes precedence when both exist,
which is a silent trap (REQ-CB-2).
