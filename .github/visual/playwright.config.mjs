// Visual regression — SCAFFOLD ONLY, deliberately not wired into CI yet.
//
// specs/007 §3.4 names the tooling so it gets built: Playwright screenshots, three
// viewports, both themes, compared with pixelmatch against committed baselines. Naming
// it is the point — "we should do visual regression" never ships.
//
// What is NOT here, and why: baselines. Every baseline captured today would be a
// screenshot of a foundation stub, and three other workstreams are changing the
// stylesheet, the code block and the templates concurrently. A golden set generated
// against that gets regenerated wholesale on the first real commit, which teaches
// everyone that "just re-approve the goldens" is the normal response to a red diff —
// and at that point the suite has negative value. Capture the first baselines at the M4
// visual freeze, per docs/verification.md.
//
// Run it (once dependencies are installed, which is NOT done in this repo — ADR-1 keeps
// the theme free of Node):
//
//     npx playwright test --config .github/visual/playwright.config.mjs
//
// Everything below that could drift between machines is pinned, because an unpinned
// visual suite reports font-rendering differences as regressions and gets switched off.

import { defineConfig, devices } from "@playwright/test";

// Pin the browser build. `npx playwright install --with-deps chromium` installs the
// revision that ships with the pinned @playwright/test version, so the version pin lives
// in package.json alongside pixelmatch — see docs/verification.md for the intended pins.
export default defineConfig({
  testDir: "./tests",
  snapshotDir: "./baselines",
  outputDir: "./results",
  fullyParallel: false,          // deterministic ordering; screenshots are cheap
  forbidOnly: true,
  retries: 0,                    // a flaky screenshot is a bug in the mask, not a retry
  reporter: [["list"], ["html", { outputFolder: "./report", open: "never" }]],

  // Serve the built exampleSite. The demo, never production citizix (specs/009 §3).
  webServer: {
    command:
      "hugo --source ../../exampleSite --themesDir \"$(cd ../.. && dirname \"$PWD\")\" " +
      "--theme \"$(cd ../.. && basename \"$PWD\")\" --destination ../../public-visual " +
      "--cleanDestinationDir --gc --minify && " +
      "python3 -m http.server 1313 --directory ../../public-visual",
    url: "http://127.0.0.1:1313/",
    reuseExistingServer: false,
    timeout: 120_000,
  },

  use: {
    baseURL: "http://127.0.0.1:1313",
    // Pinned rendering environment. Each of these changes pixels if left to the machine.
    deviceScaleFactor: 1,
    colorScheme: "light",              // per-project override below
    reducedMotion: "reduce",           // no animation mid-capture; also the a11y default
    timezoneId: "UTC",
    locale: "en-GB",
    javaScriptEnabled: true,
  },

  expect: {
    toHaveScreenshot: {
      // Explicit, not "whatever looked fine". Anti-aliasing on text moves a few pixels
      // between runs on the same machine; a real regression moves far more than this.
      maxDiffPixelRatio: 0.002,
      threshold: 0.15,               // per-pixel colour distance, pixelmatch semantics
      animations: "disabled",
      caret: "hide",
      scale: "device",
    },
  },

  // 3 viewports × 2 themes = 6 projects (specs/007 §3.4).
  projects: [
    { name: "mobile-light",  use: { ...devices["Desktop Chrome"], viewport: { width: 360,  height: 800 }, colorScheme: "light" } },
    { name: "mobile-dark",   use: { ...devices["Desktop Chrome"], viewport: { width: 360,  height: 800 }, colorScheme: "dark"  } },
    { name: "tablet-light",  use: { ...devices["Desktop Chrome"], viewport: { width: 768,  height: 1024 }, colorScheme: "light" } },
    { name: "tablet-dark",   use: { ...devices["Desktop Chrome"], viewport: { width: 768,  height: 1024 }, colorScheme: "dark"  } },
    { name: "desktop-light", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 }, colorScheme: "light" } },
    { name: "desktop-dark",  use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 }, colorScheme: "dark"  } },
  ],
});

// ── The capture list, which is the part that actually matters ────────────────────────
//
// specs/007 §3.4 is explicit that INTERACTION STATES must be captured, not just page
// loads, because every one of these has broken in a real theme without a page-load
// screenshot noticing:
//
//   focused copy button · copied confirmation · wrap toggle on and off ·
//   mobile navigation open · active TOC item · tabs with and without JS ·
//   search results
//
// Fixture pages to capture, and what each is for (specs/007 §2):
//
//   /posts/code-block-smoke-test/   every fence shape; the 854-char line; the
//                                   `systemctl status` block, which is in this set
//                                   SPECIFICALLY to catch a font-subset regression —
//                                   `└ ├ ─ ●` falling back to another font is a visual
//                                   change no unit test sees
//   /posts/code-blocks-158/         per-block chrome at the corpus maximum
//   /posts/code-block-767-lines/    copy button reachability on a very tall block
//   /posts/tables-and-data/         table overflow at 360 px
//   /posts/admonitions-and-callouts/  alert rendering, once the blockquote hook lands
//   /posts/prose-only-no-code/      the no-code case, and TOC with late headings
//   /posts/rtl-bidirectional-text/  bidi: LTR code inside RTL prose
//   /                               home and list views
//
// Masks for dynamic regions: reading time, dates rendered relative to now, and the
// fingerprinted asset hashes if they are ever surfaced in the page.
