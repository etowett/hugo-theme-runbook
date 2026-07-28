---
title: "Images and figures"
date: 2026-07-28
description: "The one fixture that exercises render-image. It exists because the reference archive cannot."
tags: ["fixtures"]
categories: ["Meta"]
---

The reference archive contains **zero** Markdown body images across 497 posts, and exactly one post
sets a cover image. That is why no list view reserves an image slot
([ADR-7](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md)).

It is also why this page has to exist. `render-image.html` is a capability Runbook ships for
third-party consumers, and a capability with no fixture is a capability nobody is testing. CI builds
with `--printUnusedTemplates --panicOnWarning`, so a shipped template that no fixture reaches fails
the build — deliberately. This is the Layer 1 case for exactly the situation
[007 §2](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/007-verification.md)
describes: synthetic fixtures cover what the archive cannot.

## A page-bundle image

Resolved through `.PageInner.Resources.GetMatch`, so `width` and `height` are read from the real
file and the browser can reserve the box before the bytes arrive. That is what keeps this off the
CLS budget.

![A checkerboard test pattern](diagram.png)

## The same image with a title, which makes it a figure

A Markdown title — the third argument — produces a real `<figure>` and `<figcaption>` rather than a
`title` attribute nobody sees.

![A checkerboard test pattern](diagram.png "Rendered as a figure with a caption")

## A remote destination

Nothing local to measure, so `width` and `height` are correctly omitted rather than guessed. The
image is deliberately not fetched at build time — the theme adds zero third-party hosts, and a
fixture must not be the exception that puts one in the budget.

![A remote image that is never fetched](https://example.com/not-fetched.png)
