---
title: "Archive"
layout: "archive"
description: "Every post, grouped by year — the fixture for layouts/archive.html."
---

Hugo has no "archive" page kind, so this template is selected by front matter rather than by
convention. This page is that selection, and it is also the fixture that proves the template is
reachable — CI builds with `--printUnusedTemplates --panicOnWarning`, so a layout the theme ships
and no fixture selects fails the build.

Deliberately not paginated: the point of an archive is that everything is on one page and findable
with the browser's own find-in-page, which pagination destroys.
