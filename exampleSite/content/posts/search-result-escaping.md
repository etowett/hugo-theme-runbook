---
title: 'Escaping fixture: <script>alert("xss")</script> & <img src=x onerror=alert(1)> in a title'
date: 2024-02-11T09:00:00Z
description: 'Hostile metadata fixture — the description carries markup too: <script>alert("desc")</script> and an unbalanced " quote.'
tags:
  - "security"
  # Hostile but slug-safe. A term containing `/` builds a nested term directory,
  # which is a Hugo-taxonomy curiosity rather than anything this fixture is testing.
  - '<img src=x onerror=alert(1)> tag'
categories:
  - "Meta"
---

This post exists to be **indexed**, not to be read.

Search results are the one place in Runbook where author-controlled text is written into the
DOM by JavaScript, and [008 §M5](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/008-milestones.md)
names search-result escaping in the security review. A rule that is only enforced by review
gets broken the first time someone adds highlighting, so the rule is backed by this fixture
instead: its title, description and one of its tags contain live markup, and every build sends
all three through the whole pipeline —

`layouts/search.json` → `/search/index.json` → `fetch` → the scorer → the `<mark>`
highlighter → the DOM.

Two independent things have to hold for that to be safe, and they fail differently:

1. **Hugo's side.** `jsonify` escapes the title into the JSON string. If that broke, the index
   would be invalid JSON and the search page would show its error state, which is loud.
2. **The chunk's side.** `assets/js/search/index.js` builds every result out of
   `document.createElement` and `textContent`. There is no `innerHTML` in that file. If that
   broke, the index would still be perfectly valid and the page would still look fine — right
   up until it executed. That is the failure this fixture is aimed at, because it is the one
   nothing else would catch.

Verify it by hand: build the demo, open `/search/?q=escaping`, and check that the title renders
as literal text with no alert and no injected element.

```sh
# The index must carry the tag as data, escaped, and never as markup.
grep -o '<script>alert' public/search/index.json | head -1
```

The tag on this post is deliberately ugly for the same reason: it proves the term list is
escaped on the way through `utils/term-title.html` as well as in the result row. Note that the
description above loses its payload before the index is written — Hugo's `plainify` discards
the *contents* of a `<script>` element, not just its tags — which is a useful second layer, and
exactly why the fixture's proof rests on the **title**, which is never plainified.
