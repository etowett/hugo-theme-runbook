#!/usr/bin/env python3
"""Performance budget gate — specs/005, specs/007 §3.2.

Two kinds of budget, with different owners, and conflating them is what broke the
original plan:

**Theme-shell budgets are hard ceilings.** They measure only what the theme emits, so
they are read off a synthetic minimal-content fixture page. CSS, core JS, the number of
executable script tags, the number of third-party hosts. If one of these regresses, the
theme got heavier, and that is always the theme's fault.

**Page-weight budgets are distribution gates.** p50 / p90 / no-regression across a
corpus, *never* a universal ceiling. A theme cannot compress content: a post with 5,756
prose words and a 767-line code block will not fit under a fixed byte cap no matter how
good the theme is. Measured against the real archive, only 22 of 493 articles were under
the originally proposed 7 KB ceiling *before Runbook added a single byte*.

    ⚠️  THE PAGE-WEIGHT THRESHOLDS ARE PLACEHOLDERS AND ARE NOT ENFORCED.

    specs/005 §3.2 gives p50 ≤ 9,000 B and p90 ≤ 14,000 B. Do not copy those numbers.
    They were set against a Stack baseline of 10,663 B median that the reference site
    has since improved past — the median is now 9,159 B *without Runbook existing*, so
    the p50 gate would measure nothing and the p90 gate is already met. specs/005 §3.1
    carries an explicit "Re-baseline required before M3" warning saying exactly this.

    The mechanism below is complete and tested. The numbers must be re-derived from a
    fresh Stack baseline captured at the same commit as the comparison — see
    `--write-baseline` and docs/verification.md.

Compression is ``gzip -n -9`` throughout. **The ``-n`` is mandatory.** Without it gzip
writes a modification timestamp into the header, byte counts move between runs, and the
gate goes flaky. A budget check that omits it is not reproducible (specs/005 §5).

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import gzip as gzip_mod
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

# ── Theme-shell budgets — HARD CEILINGS (specs/005 §3.1) ──────────────────────────────
CSS_GZ_MAX = 8_000
CORE_JS_GZ_MAX = 3_000
SEARCH_JS_GZ_MAX = 3_000
FONT_SUBSET_MAX = 30 * 1024
EXECUTABLE_SCRIPTS_MAX = 2       # see SCRIPT-TAG DECISION below
THIRD_PARTY_HOSTS_MAX = 0

# ── Page-weight budgets — PLACEHOLDERS, NOT ENFORCED (specs/005 §3.2) ─────────────────
# Enforced only with --enforce-page-weight, which nothing passes yet. Re-derive these
# from a fresh baseline before turning them on. See the module docstring.
PLACEHOLDER_PAGE_WEIGHT = {
    "article_p50": None,   # specs/005 says 9,000 — stale, see above
    "article_p90": None,   # specs/005 says 14,000 — stale, already met by Stack
    "homepage": None,      # specs/005 says 6,000
    "list_page": None,     # specs/005 says 6,000
}
# How much a page may grow against a recorded baseline before it counts as a regression.
REGRESSION_TOLERANCE = 0.02   # 2%

# ── SCRIPT-TAG DECISION ───────────────────────────────────────────────────────────────
# specs/005 §3.1 budgets "<script> tags per article: <= 2" and the build emits three:
# the inline theme guard, the deferred bundle, and <script type="application/ld+json">.
#
# The budget counts EXECUTABLE scripts only, so the real count is 2 and the budget is
# met. Rationale: the budget exists to bound parse/execute cost and main-thread blocking.
# An ld+json block is a data island — the HTML spec classifies it as a data block, the
# browser never passes it to the JavaScript engine, it triggers no network fetch and it
# blocks nothing. Counting it would either force the theme to drop structured data to
# satisfy an arithmetic target, or push someone to quietly raise the number to 3 later,
# at which point the budget no longer says what it meant.
#
# So: any <script> whose `type` is absent, empty, a JavaScript MIME type, or "module" is
# executable and counted. Everything else (ld+json, importmap, speculationrules,
# text/template) is data and is reported separately but not counted.
# Written up in docs/verification.md so the number cannot be silently redefined.
EXECUTABLE_SCRIPT_TYPES = {
    "", "module",
    "text/javascript", "application/javascript", "application/ecmascript",
    "text/ecmascript", "application/x-javascript",
}

# Attributes that cause the browser to fetch a subresource. Anchor `href` is deliberately
# absent: a link to github.com in post prose is content, not a host the theme added.
SUBRESOURCE_LINK_RELS = {
    "stylesheet", "preload", "preconnect", "dns-prefetch", "prefetch",
    "modulepreload", "icon", "apple-touch-icon", "manifest",
}
CSS_URL_RE = re.compile(r"""url\(\s*['"]?(https?://[^)'"\s]+)""", re.IGNORECASE)
CSS_IMPORT_RE = re.compile(r"""@import\s+(?:url\()?\s*['"](https?://[^'"]+)""", re.IGNORECASE)

_GZIP_BIN = shutil.which("gzip")


def gz_size(data: bytes) -> int:
    """Bytes after ``gzip -n -9``.

    Shells out to the real gzip so the number matches the command every spec and every
    prior measurement quotes. GNU gzip and zlib can differ by a few bytes on the same
    input, and a budget you cannot reproduce by hand is not a budget. Falls back to
    zlib with mtime=0 (the ``-n`` equivalent) only if gzip is unavailable.
    """
    if _GZIP_BIN:
        proc = subprocess.run([_GZIP_BIN, "-n", "-9", "-c"], input=data, capture_output=True)
        if proc.returncode == 0:
            return len(proc.stdout)
    return len(gzip_mod.compress(data, compresslevel=9, mtime=0))


def gz_file(path: Path) -> int:
    return gz_size(path.read_bytes())


class PageParser(HTMLParser):
    """Collect script tags and subresource URLs from one page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.executable_scripts = []   # list of src or "(inline)"
        self.data_scripts = []         # list of type=
        self.subresources = []         # list of URL strings
        self._script_type = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            stype = a.get("type", "").strip().lower().split(";")[0]
            if stype in EXECUTABLE_SCRIPT_TYPES:
                self.executable_scripts.append(a.get("src", "(inline)"))
            else:
                self.data_scripts.append(stype)
            if "src" in a:
                self.subresources.append(a["src"])
        elif tag == "link":
            rels = {r.strip().lower() for r in a.get("rel", "").split()}
            if rels & SUBRESOURCE_LINK_RELS and a.get("href"):
                self.subresources.append(a["href"])
        elif tag in ("img", "iframe", "video", "audio", "source", "embed", "track"):
            for attr in ("src", "poster"):
                if a.get(attr):
                    self.subresources.append(a[attr])
            for candidate in a.get("srcset", "").split(","):
                url = candidate.strip().split(" ")[0]
                if url:
                    self.subresources.append(url)


def percentile(values, q):
    """Nearest-rank percentile — no interpolation, so the answer is always a real page."""
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, round(q / 100 * len(ordered) + 0.5) - 1))
    return ordered[idx]


def resolve_local(build: Path, url: str):
    """Map a same-origin URL from a built page back to the file on disk."""
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = parsed.path
    if not path.startswith("/"):
        return None
    candidate = build / path.lstrip("/")
    return candidate if candidate.is_file() else None


class Report:
    def __init__(self):
        self.fails = []
        self.todos = []
        self.lines = []

    def row(self, name, value, budget, unit="B gz", enforce=True):
        if value is None:
            self.todos.append(f"{name}: not present in the build yet")
            self.lines.append(f"  {name:<34} {'—':>10}  budget {budget:>7}  TODO not built yet")
            return
        ok = budget is None or value <= budget
        if budget is None:
            verdict = "no gate (placeholder)"
        elif ok:
            verdict = f"ok ({budget - value:+d})"
        else:
            verdict = f"OVER by {value - budget}"
        self.lines.append(
            f"  {name:<34} {value:>10,}  budget {budget if budget is not None else '—':>7}  {verdict}"
        )
        if enforce and budget is not None and not ok:
            self.fails.append(f"{name}: {value:,} {unit} exceeds budget {budget:,}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_dir", type=Path, help="a built Hugo site (e.g. public/)")
    parser.add_argument(
        "--shell-fixture", default="posts/theme-shell-baseline/index.html",
        help="synthetic minimal-content page used for the theme-shell measurement "
             "(specs/005 §3.1 — the number must reflect only what the theme emits)",
    )
    parser.add_argument(
        "--article-glob", default="posts/*/index.html",
        help="which built pages count as articles for the distribution gate",
    )
    parser.add_argument(
        "--baseline", type=Path, default=None,
        help="JSON written by --write-baseline; enables the per-page no-regression rule",
    )
    parser.add_argument(
        "--write-baseline", type=Path, default=None,
        help="record this build's page weights as the comparison baseline and exit",
    )
    parser.add_argument(
        "--enforce-page-weight", action="store_true",
        help="turn the p50/p90 placeholders into hard gates. Do NOT pass this until the "
             "thresholds have been re-derived from a fresh baseline (specs/005 §3.1).",
    )
    parser.add_argument("--json", type=Path, default=None, help="also write results as JSON")
    args = parser.parse_args()

    build = args.build_dir.resolve()
    if not build.is_dir():
        print(f"FAIL: {build} is not a directory", file=sys.stderr)
        return 2
    if not _GZIP_BIN:
        print("  note: gzip binary not found, falling back to zlib (mtime=0)")

    report = Report()
    results = {"theme_shell": {}, "page_weight": {}}

    # ── Theme shell ───────────────────────────────────────────────────────────────────
    fixture = build / args.shell_fixture
    if not fixture.is_file():
        # Fall back to any article so the gate still measures something.
        candidates = sorted(build.glob(args.article_glob))
        if not candidates:
            print(f"FAIL: neither {args.shell_fixture} nor {args.article_glob} exists in {build}")
            return 2
        fixture = candidates[0]
        report.todos.append(
            f"shell fixture {args.shell_fixture} missing; measured "
            f"{fixture.relative_to(build)} instead, which includes content bytes"
        )

    page = PageParser()
    page.feed(fixture.read_text(encoding="utf-8", errors="replace"))

    print("Theme-shell budgets — hard ceilings, measured on a synthetic fixture")
    print(f"  fixture: {fixture.relative_to(build)}")

    css_total = 0
    css_found = False
    js_core = None
    third_party = set()

    for url in page.subresources:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            third_party.add(parsed.netloc)
            continue
        local = resolve_local(build, url)
        if local is None:
            continue
        if local.suffix == ".css":
            css_total += gz_file(local)
            css_found = True
            # A stylesheet may itself reach out to a third-party host.
            text = local.read_text(encoding="utf-8", errors="replace")
            for match in CSS_URL_RE.findall(text) + CSS_IMPORT_RE.findall(text):
                host = urlparse(match).netloc
                if host:
                    third_party.add(host)

    for src in page.executable_scripts:
        if src == "(inline)":
            continue
        local = resolve_local(build, src)
        if local is not None and local.suffix == ".js":
            js_core = (js_core or 0) + gz_file(local)

    report.row("CSS total", css_total if css_found else None, CSS_GZ_MAX)
    report.row("Core article JS", js_core, CORE_JS_GZ_MAX)

    search_js = sorted(build.glob("**/search*.js")) + sorted(build.glob("**/js/search/*.js"))
    report.row("Search chunk (lazy)",
               sum(gz_file(p) for p in search_js) if search_js else None, SEARCH_JS_GZ_MAX)

    fonts = sorted(build.rglob("*.woff2")) + sorted(build.rglob("*.woff"))
    if fonts:
        for font in fonts:
            report.row(f"Font {font.name[:24]}", font.stat().st_size, FONT_SUBSET_MAX, unit="B raw")
    else:
        report.row("Bundled code font subset", None, FONT_SUBSET_MAX)

    n_exec = len(page.executable_scripts)
    report.row("Executable <script> tags", n_exec, EXECUTABLE_SCRIPTS_MAX, unit="tags")
    report.row("Third-party hosts", len(third_party), THIRD_PARTY_HOSTS_MAX, unit="hosts")
    if third_party:
        report.fails.append(f"third-party hosts on the shell fixture: {sorted(third_party)}")

    for line in report.lines:
        print(line)
    if page.data_scripts:
        print(f"  ({len(page.data_scripts)} non-executable data script(s) not counted: "
              f"{', '.join(sorted(set(page.data_scripts)))} — see the SCRIPT-TAG DECISION "
              f"in this file and docs/verification.md)")

    results["theme_shell"] = {
        "fixture": fixture.relative_to(build).as_posix(),
        "css_gz": css_total if css_found else None,
        "core_js_gz": js_core,
        "executable_scripts": n_exec,
        "data_scripts": len(page.data_scripts),
        "third_party_hosts": sorted(third_party),
    }

    # Every article must also respect the script-tag budget, not just the fixture.
    over_budget_pages = []
    weights = {}
    for path in sorted(build.glob(args.article_glob)):
        rel = path.relative_to(build).as_posix()
        html = path.read_text(encoding="utf-8", errors="replace")
        pp = PageParser()
        pp.feed(html)
        if len(pp.executable_scripts) > EXECUTABLE_SCRIPTS_MAX:
            over_budget_pages.append((rel, len(pp.executable_scripts)))
        weights[rel] = gz_size(path.read_bytes())

    if over_budget_pages:
        for rel, n in over_budget_pages[:10]:
            report.fails.append(f"{rel}: {n} executable script tags (budget {EXECUTABLE_SCRIPTS_MAX})")

    # ── Page weight ───────────────────────────────────────────────────────────────────
    print()
    print("Page-weight budgets — distribution gates, never a universal ceiling")
    if not weights:
        # Loud, not a quiet line. The default glob is `posts/*/index.html`, which matches
        # NOTHING on a site using flat `/:slug/` permalinks — which the reference archive
        # does for all 490 posts. The distribution gate then measured zero pages and the
        # script still printed PASS, so the one gate that watches real page weight was
        # silently not running. A check that measures nothing must say so.
        print(f"  no pages matched {args.article_glob}")
        report.todos.append(
            f"article glob {args.article_glob!r} matched no pages in {build} — the page-weight "
            f"distribution gate did NOT run. Pass --article-glob for this site's permalink "
            f"shape (a flat /:slug/ site wants '*/index.html')"
        )
    else:
        values = list(weights.values())
        p50 = percentile(values, 50)
        p90 = percentile(values, 90)
        worst_page = max(weights, key=weights.get)
        print(f"  {len(values)} article page(s)")
        print(f"    p50 {p50:>8,} B gz    placeholder gate: {PLACEHOLDER_PAGE_WEIGHT['article_p50']}")
        print(f"    p90 {p90:>8,} B gz    placeholder gate: {PLACEHOLDER_PAGE_WEIGHT['article_p90']}")
        print(f"    max {max(values):>8,} B gz    ({worst_page})")
        print(f"    min {min(values):>8,} B gz")
        results["page_weight"] = {
            "p50": p50, "p90": p90, "max": max(values), "min": min(values),
            "pages": weights,
        }

    home = build / "index.html"
    if home.is_file():
        home_gz = gz_file(home)
        print(f"  homepage      {home_gz:>8,} B gz    placeholder gate: "
              f"{PLACEHOLDER_PAGE_WEIGHT['homepage']}")
        results["page_weight"]["homepage"] = home_gz

    list_pages = {
        p.relative_to(build).as_posix(): gz_file(p)
        for p in sorted(build.glob("tags/*/index.html")) + sorted(build.glob("categories/*/index.html"))
    }
    if list_pages:
        worst = max(list_pages.values())
        print(f"  taxonomy list {worst:>8,} B gz    placeholder gate: "
              f"{PLACEHOLDER_PAGE_WEIGHT['list_page']} (worst of {len(list_pages)})")
        results["page_weight"]["list_pages"] = list_pages

    print()
    print("  ⚠️  Page-weight thresholds are PLACEHOLDERS and are not enforced. specs/005 §3.1")
    print("      says re-baseline before M3: the p50 gate of 9,000 B was set against a")
    print("      10,663 B Stack median that is now 9,159 B, so it measures nothing.")
    print("      Re-derive from a fresh baseline — see docs/verification.md.")

    if args.enforce_page_weight:
        for key, budget in PLACEHOLDER_PAGE_WEIGHT.items():
            if budget is None:
                report.fails.append(
                    f"--enforce-page-weight was passed but `{key}` is still a placeholder. "
                    "Re-derive it from a fresh baseline first."
                )

    # ── No-regression rule ────────────────────────────────────────────────────────────
    if args.write_baseline:
        args.write_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.write_baseline.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(f"\nBaseline written to {args.write_baseline}")
        return 0

    if args.baseline:
        if not args.baseline.is_file():
            print(f"\n  TODO: no baseline at {args.baseline} — the per-page no-regression")
            print("        rule is inert. Generate one with --write-baseline against the")
            print("        comparison build at the SAME commit (specs/005 §3.1).")
        else:
            old = json.loads(args.baseline.read_text())
            old_pages = old.get("page_weight", {}).get("pages", {})
            regressions = []
            for rel, now in weights.items():
                before = old_pages.get(rel)
                if before and now > before * (1 + REGRESSION_TOLERANCE):
                    regressions.append((rel, before, now))
            print(f"\n  no-regression: {len(weights)} pages vs baseline, "
                  f"{len(regressions)} regression(s) over {REGRESSION_TOLERANCE:.0%}")
            for rel, before, now in sorted(regressions, key=lambda r: r[2] - r[1], reverse=True)[:10]:
                report.fails.append(
                    f"{rel} grew {before:,} → {now:,} B gz (+{(now / before - 1):.1%})"
                )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")

    print()
    for todo in report.todos:
        print(f"  TODO: {todo}")
    if report.fails:
        print(f"FAIL: {len(report.fails)} budget violation(s)")
        for f in report.fails:
            print(f"  - {f}")
        return 1
    print("PASS: budgets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
