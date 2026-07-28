---
title: "Theme shell baseline"
date: 2026-07-20
description: "The synthetic minimal-content fixture the theme-shell budgets are measured against."
tags: ["fixtures"]
categories: ["Meta"]
---

This page exists to be measured, not read.

specs/005 §3.1 requires the theme-shell budgets — CSS bytes, core JS bytes, executable script tags,
third-party hosts — to be taken against a **synthetic fixture with fixed, minimal content**, so the
number reflects only what the theme emits. Measuring them on a real article folds content bytes into
a figure that is supposed to be about the theme.

So: one paragraph, one two-line code block, one inline `span`, and nothing else. Changing this page
changes the baseline, which is why `scripts/check_budgets.py` names it explicitly rather than
picking whichever article sorts first.

```sh
sudo systemctl enable --now redis
redis-cli ping
```
