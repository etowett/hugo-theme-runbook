# Extending Runbook without forking it

**Status:** stub — owned by the templates workstream.

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

## To document

- giscus **and** Disqus comment snippets, copy-pasteable. Both, not just giscus: the reference
  deployment has years of existing Disqus threads, and a giscus-only theme would force it to choose
  between losing that history and hacking the theme
  ([Q5](../specs/006-architecture-decisions.md#q5--comments--ship-zero-providers-ship-one-hook))
- GA4 / GTM / AdSense injection, with IDs staying in site config
- Adding structured data via `custom-schema.html` — and **REQ-SEO-1 applies there too**: build a
  map, `jsonify` once, mark it `safeJS`. Never interpolate a field into a JSON literal inside a
  `<script>`; Go's `html/template` double-encodes it and the result still parses, so nothing tells
  you ([004 §2a](../specs/004-hugo-mechanics.md))
- CSS custom-property overrides as the supported way to restyle, versus forking a stylesheet
- Which `--rb-*` tokens are safe to override and which are internal
- The upgrade and deprecation policy for these hooks
