# 010 — citizix.com migration and cutover

**Status:** specification
**Last revised:** 2026-07-28

---

## 1. Prerequisite: fix two content bugs first

Both are live rendering bugs on citizix.com today, both are one-line fixes, and both belong in the
citizix repo — **not** in the theme, and not as theme fixtures. Fix them before migration work so the
before/after comparison is clean.

**Bug 1 — unterminated fence.**
`content/post/2022-03-03-how-to-install-and-configure-puppet-7-server-on-ubuntu-20-04.md:268` opens a
fence with four backticks and closes at line 270 with three. CommonMark requires the closing fence to
be at least as long as the opening one, so the block never closes and **everything from line 269 to
end-of-file renders inside a single code block**. Fix: change ` ````sh ` to ` ```sh `.

**Bug 2 — last indented block.**
`content/post/2021-08-24-how-to-install-and-configure-postgres-13-on-centos-8.md:135-136` is
5-space-indented command output. Fix: wrap it in a ` ```text ` fence. This removes the last bare
`<pre><code>` in the entire build.

**Also: teach the sanity checker this class of bug.** `scripts/content_sanity.py` should detect fence
**length** mismatches, not just odd fence counts. PR #60's checker provably misses this class — it
found three unbalanced-fence posts by counting odd numbers of ` ``` ` markers, and this file has an
even count (56) with a length mismatch.

## 2. URL parity — smaller than it looks, but verify it

**Post URLs are theme-independent.** 494 of 497 posts pin their own `url:` in front matter, and
front matter cannot be changed by a theme. The configured `permalinks.post: /p/:slug/` is entirely
unused — the build produces no `/p/` directory at all.

**The "355 aliases" are not a migration burden.** Of 354 meta-refresh pages in the build, **351 are
Hugo's automatic `/page/1/` paginator aliases** that any theme regenerates. Only **3** come from
front matter (`aliases:` on the about page).

**What genuinely can regress** is everything the theme *does* control:

| Surface | Risk |
|---|---|
| `/categories/{term}/` and `/tags/{term}/` | Taxonomy URL shape is theme/config dependent |
| `/page/{n}/` | Pagination structure and page size |
| `/search/` | Page must continue to exist at this path |
| RSS feed paths and item URLs | Output format configuration |
| Canonical URLs, OG `url`, JSON-LD `mainEntityOfPage` | Template-generated |
| Sitemap entries | citizix overrides `layouts/sitemap.xml` with image-extension and priority logic |

**Verification gate.** Emit and diff a manifest from both the Stack build and the Runbook build
covering every output URL, canonical, alias target, RSS item URL, sitemap URL, OG URL and JSON-LD
`mainEntityOfPage`. Allow only reviewed differences. Then crawl internal links against the
production-equivalent build.

## 3. The real migration checklist: 10 override files

"Replace Stack" understates the site-specific surface. citizix carries ten local layout overrides.
Each must be classified as **generic Runbook capability**, **documented extension hook**, or
**citizix-only site code**.

| File | Disposition |
|---|---|
| `layouts/_default/baseof.html` | Runbook capability — including `lang` and `dir`, which must not regress |
| `layouts/home.html` | Runbook capability |
| `layouts/shortcodes/admonition.html` | Runbook capability. Move its CSS out of per-page inline output into the budgeted main stylesheet |
| `layouts/partials/head/custom.html` | → `custom-head.html` extension hook (ADR-8) |
| `layouts/partials/head/schema.html` | Runbook capability, **with `articleBody` removed** (§4) |
| `layouts/partials/head/script.html` | → `custom-head.html` / `custom-body-end.html` |
| `layouts/partials/google-tag-manager-body.html` | → `custom-body-start.html`. No live IDs in the theme |
| `layouts/_partials/helper/external.html` | citizix-only site code |
| `layouts/_partials/article/components/photoswipe.html` | **Delete** — zero body images in the corpus (ADR-7) |
| `layouts/sitemap.xml` | Evaluate: is the image-extension and priority logic a Runbook capability or citizix-only? |

Plus:

- **Disqus thread continuity.** citizix runs Disqus with years of threads. Runbook ships a
  `comments.html` hook and a documented Disqus snippet — see
  [006](006-architecture-decisions.md) Q5. This is why a giscus-only theme was rejected.
- **GA4 / GTM / AdSense** injection through extension points, with IDs staying in site config.
- **Front-matter param mapping** — Stack's `image` and `toc: false` must map to Runbook equivalents
  or be explicitly documented as dropped.
- **`markup.highlight` config cleanup.** Set `lineNos: false` and `lineNumbersInTable: false` in
  citizix's own config as part of cutover. Runbook is correct regardless
  ([004](004-hugo-mechanics.md) REQ-CB-1), but leaving the site config wrong is a trap for anyone
  who later bypasses the hook.

## 4. Free wins available at cutover

Two changes that are pure improvement and cost nothing:

**Remove `articleBody` from JSON-LD.** `layouts/partials/head/schema.html:52` emits
`{{ $.Plain | jsonify }}`, duplicating the entire article as structured data. It costs more gzipped
bytes than every line-number table on the page combined, with no verified SEO benefit.

**Fix the double-encoded JSON-LD values.** The current template emits malformed values — the puppet
page produces `"headline":"\"How to …\""` and `"datePublished":"\"2022-03-03T21:55:03Z\""`. Shipping
correct JSON-LD is simultaneously a validity fix and the single largest article-HTML saving
available.

## 5. Cutover procedure

1. Fix the two content bugs (§1). Merge separately, before any theme work.
2. Build citizix with Runbook in CI; run the full parity manifest diff (§2).
3. Deploy to a **preview host** with `noindex`, and review it against production page-by-page for the
   pinned fixture set.
4. Run the link crawl and the budget distribution gates against the preview.
5. Cut over production. citizix deploys via manual `workflow_dispatch` only — this is deliberate and
   must not be automated.
6. **Rollback plan:** the theme is a submodule pin, so rollback is a submodule revert plus a redeploy.
   Define the rollback trigger (any URL parity failure, any 5xx, any Lighthouse regression beyond
   threshold) and confirm the rollback command before cutover, not after.
7. Observe production for a defined period before submitting to the showcase.

## 6. Sequencing note

The showcase submission comes **after** citizix cutover, and the showcase demo is the deployed
`exampleSite` — never citizix, which carries advertising and analytics that the showcase forbids.
See [009](009-showcase-compliance.md) §3.
