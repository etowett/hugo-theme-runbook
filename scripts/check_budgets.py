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

The page-weight thresholds are derived from the pinned Runbook archive with 5% headroom
and enforced by parity.yml through --enforce-page-weight. exampleSite reports them only —
synthetic fixtures are not the archive. See docs/verification.md §4 for the values and
the re-pin procedure. Runs without enforcement name the inactive rules in their verdict.

Compression is ``gzip -n -9`` throughout. **The ``-n`` is mandatory.** Without it gzip
writes a modification timestamp into the header, byte counts move between runs, and the
gate goes flaky. A budget check that omits it is not reproducible (specs/005 §5).

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import gzip as gzip_mod
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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

# ── Page-weight budgets — archive distribution gates (specs/005 §3.2) ────────────────
# Runbook side, CITIZIX_REF c98c01b, run 42674523402, +5% rounded up.
# Re-derive when CITIZIX_REF moves — docs/verification.md §4.
PAGE_WEIGHT_THRESHOLDS = {
    "article_p50": 7_539,   # 7,180 B gz × 1.05, ceil
    "article_p90": 10_904,  # 10,384 B gz × 1.05, ceil
    "homepage": 5_357,      # 5,101 B gz × 1.05, ceil
    "list_page": 4_744,     # 4,518 B gz × 1.05, ceil
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

# ── THE LAZY SEARCH CHUNK — ONE DEFINITION, TWO CONSUMERS ─────────────────────────────
# The chunk is budgeted separately, at SEARCH_JS_GZ_MAX, because it is loaded only on
# /search/ — everything reachable from runbook.js shares one 3 KB budget and the search
# entry has its own. That allowance and the per-page script-tag rule used to derive "is
# this the search chunk" independently, and disagreed: the byte budget granted the chunk
# its own 3 KB and the per-page sweep then failed search/index.html for carrying a third
# executable <script> tag, against a ceiling read off a synthetic fixture that loads no
# search at all (issue #51). A budget that grants a feature an allowance and then
# penalises the one page that uses it is not measuring anything.
#
# Both consumers now resolve the chunk through find_search_chunk(), so they cannot drift
# apart again. The exclusion is scoped to the per-page sweep and deliberately NOT applied
# to the shell-fixture row — see the comment there.
SEARCH_CHUNK_GLOBS = ("**/search*.js", "**/js/search/*.js")

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
        self.refresh = False           # <meta http-equiv="refresh"> — a Hugo alias stub
        self._script_type = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta" and a.get("http-equiv", "").strip().lower() == "refresh":
            self.refresh = True
        elif tag == "script":
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


def find_search_chunk(build: Path):
    """Every built file that is the lazy search chunk — the single definition (see above).

    Both globs are the pair this gate has always carried. The current pipeline emits
    `js/search/index.<hash>.js`; the flat `search*.js` spelling is kept so a rename cannot
    drop the chunk out of both rules at once. The result is a set rather than a
    concatenation — no build has yet emitted a file matching both patterns, and a set makes
    it impossible to weigh one twice against SEARCH_JS_GZ_MAX if one ever does.
    """
    found = set()
    for pattern in SEARCH_CHUNK_GLOBS:
        found.update(p for p in build.glob(pattern) if p.is_file())
    return sorted(found)


def counted_scripts(build: Path, page: "PageParser", search_chunk):
    """A page's executable ``<script>`` tags for the per-page budget, minus the search chunk.

    Per-page is a corpus rule and the corpus contains /search/, which is *supposed* to load
    the chunk; the chunk is weighed against its own budget instead. An inline script is
    never the chunk, and a src the build cannot resolve to a local file is not either — a
    consumer's third-party tag counts, which is the point.
    """
    chunk = set(search_chunk)
    counted = []
    for src in page.executable_scripts:
        local = None if src == "(inline)" else resolve_local(build, src)
        if local is not None and local in chunk:
            continue
        counted.append(src)
    return counted


def read_page(path: Path) -> PageParser:
    page = PageParser()
    page.feed(path.read_text(encoding="utf-8", errors="replace"))
    return page


def is_article(path: Path, page: PageParser) -> bool:
    """Whether a page matched by ``--article-glob`` is an article — the single definition.

    The shell-fixture fallback and the per-page sweep both route through this (issue #64).
    On a flat ``/:slug/`` archive the glob is ``*/index.html``, which also matches Hugo
    alias stubs and taxonomy lists; the fallback then measured a 243-byte redirect as the
    theme shell, and ``/tags/`` failed the no-regression rule for a reviewed change.

    The evidence has to be the same in the Stack baseline and the Runbook candidate, or the
    no-regression rule compares two different sets of pages. The theme's article type
    cannot be that evidence: Runbook's JSON-LD says ``BlogPosting`` (head/schema.html),
    and Stack's og:type says ``article`` on every regular page, About and Search included.
    Both signals used here are written by Hugo from content and site config, not by the theme:

    * an alias stub is ``<meta http-equiv="refresh">`` — Hugo's alias template, either
      theme, minified or not, and never an article;
    * a list page (home, section, taxonomy, term) gets an RSS ``index.xml`` beside its
      ``index.html``; a regular page does not. That catches ``tags/`` and ``categories/``.

    Known edges: a page whose front matter adds an ``rss`` output (the archive's /search/)
    is classified as a list, which is right for a budget sweep; a regular page outside
    ``mainSections`` such as /about-us/ still counts, because nothing theme-neutral tells it
    from a post; and a site that disables RSS, or renames it (e.g.
    ``baseName = feed``), gets the old behaviour back for its lists.
    """
    return not page.refresh and not (path.parent / "index.xml").is_file()


def shell_candidate(build: Path, path: Path, search_chunk) -> bool:
    """Whether the shell fallback may measure this page: an article that does not load the
    lazy search chunk, because the shell row counts executable tags raw and would fail it."""
    page = read_page(path)
    return (is_article(path, page)
            and len(counted_scripts(build, page, search_chunk)) == len(page.executable_scripts))


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


def gate(threshold) -> str:
    """A threshold as the log prints it, so it reads in the same units as the measurement."""
    return "unset" if threshold is None else f"{threshold:,} B gz"


def page_weight_fails(measured: dict, thresholds: dict) -> list[str]:
    """Compare archive measurements without treating an unmeasured page as zero."""
    fails = []
    for key, threshold in thresholds.items():
        value = measured.get(key)
        if value is None:
            # Unmeasured is not zero, and it is not a pass either: an archive whose glob or
            # permalinks moved at a re-pin measures nothing, and a gate that reads green on
            # nothing is the failure #45 is about.
            if threshold is not None:
                fails.append(f"{key} measured nothing under --enforce-page-weight — "
                             "nothing matched, so nothing was compared")
            continue
        if threshold is None:
            fails.append(
                f"--enforce-page-weight was passed but `{key}` is still a placeholder. "
                "Re-derive it from a fresh baseline first."
            )
        elif value > threshold:
            fails.append(f"{key} {value:,} B gz over its {threshold:,} B threshold")
    return fails


def self_test() -> int:
    """The script-tag rule, exercised in both directions against a synthetic build tree.

    Issue #51 was a false positive — /search/ failed for loading the chunk the gate had
    already granted its own budget. Fixing only that direction would convert it into a false
    negative, which is worse: a gate that cannot fail is a gate nobody looks at, and this one
    is the only thing standing between a consuming site and an analytics tag per page. So
    both directions are pinned here, against a tree built from strings rather than from a
    Hugo run, so the rule can be checked without a build and cannot rot silently.
    """
    report = Report()

    def case(name: str, ok: bool, measured: str):
        # The measurement is printed whether or not the case passes, for the same reason
        # report.row prints a value next to every budget: a green line with no number in it
        # cannot be checked by the person reading the log.
        report.lines.append(f"  {'ok  ' if ok else 'FAIL'}  {name:<62} {measured}")
        if not ok:
            report.fails.append(f"{name}: {measured}")

    def parse(html: str) -> PageParser:
        page = PageParser()
        page.feed(html)
        return page

    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp).resolve()
        (build / "js" / "search").mkdir(parents=True)
        (build / "js" / "search" / "index.deadbeef.js").write_text("// lazy search chunk\n")
        (build / "js" / "runbook.cafebabe.js").write_text("// core bundle\n")
        (build / "js" / "vendor.f00d.js").write_text("// a third script that is not search\n")

        chunk = find_search_chunk(build)
        names = [p.relative_to(build).as_posix() for p in chunk]
        case("the shared definition resolves the chunk, and only the chunk",
             names == ["js/search/index.deadbeef.js"], f"matched {names}")

        search_page = parse(
            "<script>/* theme guard */</script>"
            '<script type="application/ld+json">{}</script>'
            '<script defer src="/js/search/index.deadbeef.js"></script>'
            '<script defer src="/js/runbook.cafebabe.js"></script>'
        )
        n = len(counted_scripts(build, search_page, chunk))
        case("a page carrying the search chunk is within the per-page budget",
             n <= EXECUTABLE_SCRIPTS_MAX, f"{n} counted, budget {EXECUTABLE_SCRIPTS_MAX}")
        raw = len(search_page.executable_scripts)
        # Not the same rule: the shell row is where a chunk that stopped being lazy shows up.
        case("the shell-fixture row still counts the chunk",
             raw == 3, f"{raw} raw on the same page")

        noisy_page = parse(
            "<script>/* theme guard */</script>"
            '<script defer src="/js/runbook.cafebabe.js"></script>'
            '<script defer src="/js/vendor.f00d.js"></script>'
        )
        n = len(counted_scripts(build, noisy_page, chunk))
        case("a page carrying three non-search scripts is still over budget",
             n > EXECUTABLE_SCRIPTS_MAX, f"{n} counted, budget {EXECUTABLE_SCRIPTS_MAX}")

        offsite_page = parse(
            "<script>/* theme guard */</script>"
            '<script defer src="/js/runbook.cafebabe.js"></script>'
            '<script defer src="https://example.com/search.js"></script>'
        )
        n = len(counted_scripts(build, offsite_page, chunk))
        case("an off-site script merely named like the chunk still counts",
             n > EXECUTABLE_SCRIPTS_MAX, f"{n} counted, budget {EXECUTABLE_SCRIPTS_MAX}")

        # Article classification (issue #64) — the shapes a flat `*/index.html` glob matches.
        # The stub is Hugo's alias template as `--minify` writes it, unquoted attributes and all.
        pages = {
            "old-slug": ('<!doctype html><html lang=en-us><head><title>x</title>'
                         '<link rel=canonical href=/new-slug/><meta name=robots content="noindex">'
                         '<meta http-equiv=refresh content="0; url=/new-slug/"></head></html>', False),
            "tags": ("<article>a term</article><article>another</article>", True),
            "new-slug": ('<article class=main-article><h1>Post</h1></article>'
                         '<script type="application/ld+json">{"@type":"Article"}</script>', False),
        }
        for slug, (html, has_rss) in pages.items():
            (build / slug).mkdir()
            (build / slug / "index.html").write_text(html)
            if has_rss:
                (build / slug / "index.xml").write_text("<rss/>")
        verdict = {s: is_article(build / s / "index.html", read_page(build / s / "index.html"))
                   for s in pages}
        case("an alias stub is not an article", not verdict["old-slug"],
             f"is_article={verdict['old-slug']}")
        case("a taxonomy list (RSS beside it) is not an article", not verdict["tags"],
             f"is_article={verdict['tags']}")
        case("a real article is an article", verdict["new-slug"],
             f"is_article={verdict['new-slug']}")

        (build / "search").mkdir()
        (build / "search" / "index.html").write_text(
            '<script defer src="/js/search/index.deadbeef.js"></script>')
        ok = not shell_candidate(build, build / "search" / "index.html", chunk)
        case("the shell fallback skips a page that loads the search chunk", ok,
             f"shell_candidate={not ok}")

    # Both directions matter — set thresholds alone do not prove a gate can fail (#45).
    thresholds = {"article_p50": 100, "article_p90": 200, "homepage": 80, "list_page": 60}
    measured = {key: value - 1 for key, value in thresholds.items()}
    fails = page_weight_fails(measured, thresholds)
    case("page weight under every threshold passes", fails == [], f"fails={fails}")
    measured["article_p50"] = thresholds["article_p50"] + 1
    fails = page_weight_fails(measured, thresholds)
    case("page weight p50 one byte over fails",
         fails == ["article_p50 101 B gz over its 100 B threshold"], f"fails={fails}")
    fails = page_weight_fails({"article_p50": 99}, {"article_p50": None})
    case("page weight with a None threshold fails",
         len(fails) == 1 and "article_p50" in fails[0] and "still a placeholder" in fails[0],
         f"fails={fails}")
    fails = page_weight_fails({}, {"homepage": 1})
    case("page weight that measured nothing fails",
         len(fails) == 1 and "measured nothing" in fails[0], f"fails={fails}")
    unset = [key for key, value in PAGE_WEIGHT_THRESHOLDS.items() if value is None]
    case("shipped page-weight thresholds are all set", not unset, f"unset={unset}")

    print("Script-tag rule, article classification and page weight — regression cases (#51, #64, #45)")
    for line in report.lines:
        print(line)
    print()
    if report.fails:
        print(f"FAIL: {len(report.fails)} self-test failure(s)")
        for f in report.fails:
            print(f"  - {f}")
        return 1
    print(f"PASS: check_budgets self-test ({len(report.lines)} cases)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_dir", type=Path, nargs="?",
                        help="a built Hugo site (e.g. public/)")
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
        help="enforce the archive page-weight thresholds (docs/verification.md §4).",
    )
    parser.add_argument("--json", type=Path, default=None, help="also write results as JSON")
    parser.add_argument(
        "--self-test", action="store_true",
        help="check the script-tag rule against a synthetic build tree and exit — needs no "
             "build, so it runs before the one that would take fifteen seconds to produce",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.build_dir is None:
        parser.error("build_dir is required unless --self-test is passed")

    build = args.build_dir.resolve()
    if not build.is_dir():
        print(f"FAIL: {build} is not a directory", file=sys.stderr)
        return 2
    if not _GZIP_BIN:
        print("  note: gzip binary not found, falling back to zlib (mtime=0)")

    report = Report()
    results = {"theme_shell": {}, "page_weight": {}}

    # ── Theme shell ───────────────────────────────────────────────────────────────────
    search_js = find_search_chunk(build)
    fixture = build / args.shell_fixture
    if not fixture.is_file():
        # Fall back to any article so the gate still measures something — an article, not
        # whatever sorts first, which on a flat archive is an alias stub (issue #64).
        fixture = next((p for p in sorted(build.glob(args.article_glob))
                        if shell_candidate(build, p, search_js)), None)
        if fixture is None:
            print(f"FAIL: neither {args.shell_fixture} nor an article under "
                  f"{args.article_glob} exists in {build}")
            return 2
        report.todos.append(
            f"shell fixture {args.shell_fixture} missing; measured "
            f"{fixture.relative_to(build)} instead, which includes content bytes"
        )

    page = read_page(fixture)

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

    report.row("Search chunk (lazy)",
               sum(gz_file(p) for p in search_js) if search_js else None, SEARCH_JS_GZ_MAX)

    fonts = sorted(build.rglob("*.woff2")) + sorted(build.rglob("*.woff"))
    if fonts:
        for font in fonts:
            report.row(f"Font {font.name[:24]}", font.stat().st_size, FONT_SUBSET_MAX, unit="B raw")
    else:
        report.row("Bundled code font subset", None, FONT_SUBSET_MAX)

    # Deliberately the RAW count, with no search-chunk exclusion. The fixture is a minimal
    # page that must never carry the lazy chunk, so this row is where "the lazy chunk
    # stopped being lazy" is caught — excluding it here would hide exactly the regression
    # the shell ceiling exists for.
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

    # Every article must also respect the script-tag budget, not just the fixture — but on
    # the page the lazy search chunk is meant to load, the chunk is measured against its own
    # budget above rather than counted twice (issue #51, and the block at the top). Pages the
    # glob matches that are not articles — alias stubs, taxonomy lists — are skipped (#64).
    over_budget_pages = []
    weights = {}
    skipped = []
    for path in sorted(build.glob(args.article_glob)):
        rel = path.relative_to(build).as_posix()
        pp = read_page(path)
        if not is_article(path, pp):
            skipped.append(rel)
            continue
        counted = counted_scripts(build, pp, search_js)
        if len(counted) > EXECUTABLE_SCRIPTS_MAX:
            over_budget_pages.append((rel, len(counted)))
        weights[rel] = gz_size(path.read_bytes())

    if over_budget_pages:
        for rel, n in over_budget_pages[:10]:
            report.fails.append(f"{rel}: {n} executable script tags (budget {EXECUTABLE_SCRIPTS_MAX})")

    # ── Page weight ───────────────────────────────────────────────────────────────────
    print()
    print("Page-weight budgets — distribution gates, never a universal ceiling")
    # The Stack --write-baseline pass is measured, never gated. Printing Runbook's gates
    # beside Stack's heavier numbers reads as four failures in a job that passed.
    def show(threshold) -> str:
        return "(baseline, not gated)" if args.write_baseline else f"gate: {gate(threshold)}"
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
        print(f"  {len(values)} article page(s)"
              + (f", {len(skipped)} non-article match(es) skipped" if skipped else ""))
        print(f"    p50 {p50:>8,} B gz    {show(PAGE_WEIGHT_THRESHOLDS['article_p50'])}")
        print(f"    p90 {p90:>8,} B gz    {show(PAGE_WEIGHT_THRESHOLDS['article_p90'])}")
        print(f"    max {max(values):>8,} B gz    ({worst_page})")
        print(f"    min {min(values):>8,} B gz")
        results["page_weight"] = {
            "p50": p50, "p90": p90, "max": max(values), "min": min(values),
            "pages": weights, "skipped": skipped,
        }

    home = build / "index.html"
    if home.is_file():
        home_gz = gz_file(home)
        print(f"  homepage      {home_gz:>8,} B gz    "
              f"{show(PAGE_WEIGHT_THRESHOLDS['homepage'])}")
        results["page_weight"]["homepage"] = home_gz

    list_pages = {
        p.relative_to(build).as_posix(): gz_file(p)
        for p in sorted(build.glob("tags/*/index.html")) + sorted(build.glob("categories/*/index.html"))
    }
    if list_pages:
        worst = max(list_pages.values())
        print(f"  taxonomy list {worst:>8,} B gz    "
              f"{show(PAGE_WEIGHT_THRESHOLDS['list_page'])} (worst of {len(list_pages)})")
        results["page_weight"]["list_pages"] = list_pages

    print()
    print("  Page-weight thresholds are "
          + ("enforced (--enforce-page-weight)." if args.enforce_page_weight else "reported only."))

    if args.enforce_page_weight:
        report.fails.extend(page_weight_fails({
            "article_p50": results["page_weight"].get("p50"),
            "article_p90": results["page_weight"].get("p90"),
            "homepage": results["page_weight"].get("homepage"),
            "list_page": max(list_pages.values()) if list_pages else None,
        }, PAGE_WEIGHT_THRESHOLDS))

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

    # ── Which half of this gate is actually gating? ───────────────────────────────────
    # Archive thresholds do not measure exampleSite meaningfully, so ci.yml reports
    # them without enforcing them. Keep that distinction in the verdict and the runner
    # annotation — a bare PASS hid inactive gates for two milestones (issue #45).
    inert = []
    if not args.enforce_page_weight:
        inert.append(
            "page-weight thresholds are archive numbers and are enforced only by "
            "parity.yml (--enforce-page-weight)"
        )
    if not weights:
        inert.append(
            f"the distribution gate matched no pages under {args.article_glob!r}, so p50/p90 "
            "measured nothing at all"
        )
    if not args.baseline:
        inert.append("no --baseline was passed, so the per-page no-regression rule did not run")
    elif not args.baseline.is_file():
        inert.append(
            f"--baseline {args.baseline} does not exist, so the per-page no-regression rule "
            "did not run"
        )
    results["inert"] = inert

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
    if inert:
        print(f"PASS (page-weight gates INERT — {len(inert)} rule(s) measured but gated nothing)")
        for item in inert:
            print(f"  ! {item}")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(
                "::warning file=scripts/check_budgets.py,"
                "title=Budgets passed but the page-weight half is not gating::"
                + "; ".join(inert)
            )
        return 0
    print("PASS: budgets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
