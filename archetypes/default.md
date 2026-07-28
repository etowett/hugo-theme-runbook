+++
title = "{{ replace .File.ContentBaseName "-" " " | title }}"
date = {{ .Date }}
draft = true
description = ""
tags = []
categories = []

# Optional, per specs/003 §3.4 and ADR-7. Cover images are a capability, never a layout
# assumption — no list view reserves space for one.
# image = ""

# Optional per-page overrides of params.runbook.*
# [params]
#   toc = true
#   robots = "noindex"
+++
