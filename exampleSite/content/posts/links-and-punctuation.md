---
title: "Links, punctuation and bare URLs"
date: 2026-07-25
description: "Links followed directly by punctuation, external links for the new-tab announcement, and a bare URL longer than a phone is wide."
tags: ["fixtures", "layout"]
categories: ["Meta"]
---

The cluster runs [Kubernetes](https://kubernetes.io/), [Traefik](https://traefik.io/) and an
[internal runbook](/posts/tables-and-data/). A link followed directly by a comma, a full stop or a
closing bracket must render with no space before the punctuation, because the render hook used to
end in a newline that leaked into the page (issue #69). The same applies to [this
link](https://gohugo.io/); and to a parenthetical ([Hugo](https://gohugo.io/)).

Every external link above is also the fixture for the new-tab announcement. With
`params.runbook.externalLinksNewTab = true` each one carries a visually hidden "(opens in a new
tab)" that a screen reader announces and nobody sees. The setting is site-wide, so this page cannot
turn it on for itself; a scratch build with `HUGO_PARAMS_RUNBOOK_EXTERNALLINKSNEWTAB=true` does.

A bare URL as its own link text is one unbreakable word, and at 390 px it used to pan the whole page
sideways (issue #83). This one is 120 characters long and must wrap inside the measure:
<https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html?section=server-certificates-xyz>
