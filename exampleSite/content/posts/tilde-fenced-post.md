---
title: "A post whose first fence is a tilde"
date: 2026-07-20
description: "CommonMark allows ~~~ as well as ```. This post opens with one, which is the only way to catch a card plate that only knows backticks."
tags: ["fixtures"]
categories: ["Meta"]
series: ["Theme foundations"]
weight: 2
---

~~~sh
sudo systemctl reload nginx
sudo nginx -t
~~~

The block above is the point of this page, and it has to be the **first** one.

`list/post-item.html` builds a card's code plate by finding a post's first fenced block.
It matched only ` ``` `, so a post opening with `~~~` lost its plate silently — no error,
no warning, just a card that quietly fell back to having no picture. The card plate is
the whole premise of the list view, so "silently, on valid CommonMark" is the worst
possible failure mode for it.

Nothing in the fixture set caught it, because every other post here happens to open with
a backtick fence. That is exactly the shape of gap a corpus-derived fixture set leaves
for third-party content: the reference archive uses one convention, so the fixtures
inherit it, and the other convention is untested until somebody's site breaks.

Both delimiters reach the render hook — [004 §1](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/004-hugo-mechanics.md)
records the tilde fence firing with `.Type` set — so a reader sees a fully working code
block here while the card for this very post showed nothing.

## A backtick fence later in the same post

```yaml
server:
  listen: 8080
~~~ not a closing delimiter, because this fence opened with backticks
```

This exists to check the two patterns do not interfere: the tilde search must not match
this block, and the backtick search must not be confused by the tilde on the third line.
A single regex alternation could not express that — Go's RE2 has no backreferences, so
the closing delimiter cannot be tied to the opening one, and `[`~]{3}` would happily
close a backtick fence with a tilde.
