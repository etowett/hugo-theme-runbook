---
title: "One procedure, three package managers"
date: 2026-07-26
description: "The tabs shortcode, which stacks every panel instead of hiding two of them, and the file tree that is deliberately just a fenced block."
tags: ["fixtures", "shortcodes"]
categories: ["Meta"]
---

Installing the same thing on Debian, Fedora and openSUSE is one procedure with three package
managers, not three posts. The `tabs` shortcode groups those variants — and it does it by stacking
every one of them, not by hiding two behind a strip of buttons.

## Why nothing is hidden

[ADR-5](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md)
states it as a requirement rather than a preference: tabs expose **all** panels without JavaScript.
The theme's script bundle is frozen at three modules and tabs are not one of them, so the only
switching mechanisms available are CSS-only ones — the radio pattern, `:target`, `:has()`. Each of
them puts `display: none` on the panels the reader did not pick, and that costs four things this
theme is not willing to lose:

- **Find-in-page.** Searching the page for `zypper` finds nothing on the page that documents
  `zypper`.
- **Print and PDF.** These are procedures. They get printed. A switched strip prints one panel.
- **The search index.** The index is built from the page's text, so a hit can land a reader on a
  page where the matching words are invisible.
- **Honest semantics.** `role="tab"` needs something focusable that the browser exposes as a tab.
  A `<label>` is not focusable, and putting the role on the `<input type="radio">` instead is a
  conflict that ARIA in HTML forbids. What survives announces as a radio group whose panel change
  is never announced, because announcing it needs the script that does not exist.

So: a jump strip of ordinary same-page links, then every panel, each under a real heading. Keyboard
operation is whatever the browser does with a link, which is the correct answer. Following one also
moves the sequential-focus starting point into the panel, so the next tab press continues from the
content the reader jumped to rather than from the strip.

## The shortcode

{{< tabs title="Install nginx" >}}
{{< tab name="apt" >}}
Debian, Ubuntu and derivatives.

```sh
sudo apt update
sudo apt install -y nginx
sudo systemctl enable --now nginx
```
{{< /tab >}}
{{< tab name="dnf" >}}
Fedora, RHEL 8+, Rocky, Alma.

```sh
sudo dnf install -y nginx
sudo systemctl enable --now nginx
```

The firewall is on by default here, which the Debian instructions do not need:

```sh
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --reload
```
{{< /tab >}}
{{< tab name="zypper" >}}
openSUSE Leap and Tumbleweed.

```sh
sudo zypper --non-interactive install nginx
sudo systemctl enable --now nginx
```
{{< /tab >}}
{{< /tabs >}}

Every fenced block above is inside a shortcode. `.Inner` goes through `RenderString` in block
display, so each one still reaches `layouts/_markup/render-codeblock.html` and keeps its language
tag, its copy button and its wrap toggle — the same contract `details` relies on.

## Two panels, no title, and a custom anchor

The strip takes its accessible name from the block title when there is one and from the translated
`tabsVariants` string when there is not. A single-panel block renders the panel and skips the strip,
because a jump strip with one destination is noise.

{{< tabs id="rollback" level="3" >}}
{{< tab name="systemd" id="unit" >}}
```sh
sudo systemctl revert nginx.service
sudo systemctl daemon-reload
```
{{< /tab >}}
{{< tab name="OpenRC" >}}
```sh
sudo rc-update del nginx default
```
{{< /tab >}}
{{< /tabs >}}

The `id` on the block fixes the anchor prefix, so
[`#rb-rollback-unit`](#rb-rollback-unit) keeps working when the page is reordered. Without it the
prefix comes from the title, and failing that from the shortcode's position in the page — which
moves the moment somebody inserts a paragraph above it.

{{< tabs title="A block with one panel" >}}
{{< tab name="Only option" >}}
No strip is drawn above this one.
{{< /tab >}}
{{< /tabs >}}

## Directory trees are a fenced block, on purpose

There is no `filetree` shortcode, and that is a decision rather than an omission. The bundled
monospace subset carries `└ ├ ─ │` precisely because 44% of the reference archive draws them inside
code (REQ-FONT-1), so `tree` output already renders correctly, copies back out as exactly what
`tree` printed, and gets a copy button for free:

```text
etc/nginx/
├── conf.d/
│   └── default.conf
├── nginx.conf
├── sites-available/
│   ├── example.com
│   └── internal.example.com
└── sites-enabled/
    └── example.com -> ../sites-available/example.com
```

A shortcode that re-drew that as a nested `<ul>` would spend bytes in a stylesheet with a
theme-wide 8,000 B budget in order to produce something a reader cannot paste back into a terminal,
and it would do it for a construct the reference archive uses zero times in 497 posts. The reasoning
is written up in full in `docs/shortcodes.md`.
