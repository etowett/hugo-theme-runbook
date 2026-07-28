/* ═══════════════════════════════════════════════════════════════════════════════
   runbook.js — the single deferred entry point for an article page.

   ▸ THIS FILE IS FROZEN. Three workstreams own one module each; nobody edits the
     entry. Adding an import here is a deliberate budget decision, not a detail.

   ADR-5 — no framework, and JS is split by page ROLE rather than shipped as one
   bundle. Everything reachable from here is the "core article" chunk:

       BUDGET: <= 3,000 B gzipped, for ALL of it together.

   That budget covers the theme toggle, copy, wrap toggle and overflow detection, and
   TOC scroll-spy only if it fits — open decision #3 in specs/006 is exactly the
   question of whether it does. Measure before adding.

   Search is NOT imported here. It is a separate lazy chunk loaded only on /search/,
   with its own 3 KB budget (specs/005 §3.1).

   ── DEGRADATION IS A HARD REQUIREMENT ──────────────────────────────────────────
   Every page must be readable and navigable with JavaScript disabled (success
   criterion 6, specs/001 §5). Concretely, for the modules below:
     * copy and wrap controls are rendered `hidden` and unhidden by JS, so a
       non-functioning control is never presented;
     * code is never hidden or restructured by JS;
     * TOC anchors work without scroll-spy;
     * the theme falls back to the CSS default, which is already correct.

   A module must therefore no-op cleanly when its markup is absent, and must never
   throw — one exception here takes out every other feature on the page.
   ═══════════════════════════════════════════════════════════════════════════════ */

import { initTheme } from './modules/theme.js';
import { initCode } from './modules/code.js';
import { initToc } from './modules/toc.js';

function boot() {
  // Isolated so a failure in one module cannot disable the others.
  for (const init of [initTheme, initCode, initToc]) {
    try {
      init();
    } catch (e) {
      /* Intentionally silent in production: a broken enhancement must not surface
         as a console error on a reader's article page. */
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
