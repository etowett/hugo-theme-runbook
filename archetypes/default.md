+++
title = "{{ replace .File.ContentBaseName "-" " " | title }}"
date = {{ .Date }}
draft = true

# Used as the meta description, the Open Graph / Twitter description, the JSON-LD
# `description`, and the summary line in every list view. Without it the theme falls
# back to Hugo's generated summary, which for a procedure is the first 70 words of
# the preamble rather than what the post is about. Write it.
description = ""

tags = []
categories = []

# Optional, per specs/003 §3.4 and ADR-7. Cover images are a CAPABILITY, never a
# layout assumption: no list view reserves space for one, and nothing shifts when it
# is absent. When present it is used for Open Graph, the Twitter card and JSON-LD.
# Accepts a page resource name, a path under assets/, or an absolute URL.
# image = ""

# Series membership. Requires the consumer to register the taxonomy — a theme cannot:
#   [taxonomies]
#     series = "series"
# Reading order is the post date ascending unless posts carry an explicit `weight`.
# series = []

# ── Per-page overrides ────────────────────────────────────────────────────────
# These are read from the page's own front matter, NOT from [params], because that is
# where hugo-theme-stack put them and migrating content should not have to be
# rewritten.

# toc = false            # suppress the table of contents on this page
# robots = "noindex"     # per-page robots directive
# lastmod = ...          # surfaced as "Updated" and as JSON-LD dateModified, but only
#                        # when it is actually LATER than `date`
+++
