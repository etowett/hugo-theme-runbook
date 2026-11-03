---
title: "A crowded letter on the tags page"
date: 2026-07-26
description: "Fourteen tags under one initial, so the tags page has a pill row wider than a phone."
tags: ["kafka", "kaniko", "karpenter", "keda", "keycloak", "kibana", "kind", "kong", "krew", "k3s", "kubectl", "kubernetes", "kustomize", "kyverno"]
categories: ["Meta"]
---

This page exists for its tags. Below the mobile breakpoint the tags page lays each letter's pills in
one row that scrolls sideways, and that row sits in a grid track. A grid item's automatic minimum
width is its min-content width, so without `min-width: 0` on the group the track grows to the whole
row and the page pans instead of the row (issue #104). The reference archive hit it at 1,297 px on a
390 px phone; the demo had too few terms per letter to show it.

At 390 px, `/tags/` should have `document.documentElement.scrollWidth` equal to the viewport, and the
K row should scroll on its own. That is checked in a browser, not by a gate; `check_fixtures.py`
only guards the tag count that makes the check possible.
