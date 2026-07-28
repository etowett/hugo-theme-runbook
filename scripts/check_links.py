#!/usr/bin/env python3
"""Link gate — specs/007 §3.5. Two modes, deliberately on different schedules.

``--internal`` (default) resolves every same-origin link, subresource and in-page
fragment against the built tree. It touches no network, takes under a second, and runs on
every pull request.

``--external`` sweeps outbound absolute URLs over the network. It runs **weekly and never
per-PR**, because that is what the reference site's experience actually taught:

* Its link check excluded *every* absolute URL, so no outbound link had ever been
  verified and 12 dead ones accumulated — two pointing at repositories that no longer
  existed, one at a page that never had.
* But the sweep takes about two minutes over 8,400 links, hits rate limits, and fails
  when a third party's documentation site is down. Gating a PR on that produces a red X
  nobody can act on, which is how people learn to ignore CI.

So: weekly, opening a tracking issue on failure (.github/workflows/scheduled.yml).

Exclusions live in ``.github/link-exclusions.json`` as ``{pattern: reason}``, and the
reason is structurally mandatory — an entry with an empty reason fails this script. Two
things that mattered in practice:

* Some hosts return 403 or 418 to any automated checker while working perfectly in a
  browser. Without a recorded reason, someone tidying the list deletes a real exclusion.
* Exclude only false positives. A genuinely dead link gets fixed, not excluded.

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

DEFAULT_EXCLUSIONS = Path(".github/link-exclusions.json")
USER_AGENT = "hugo-theme-runbook-link-check/1.0 (+https://github.com/etowett/hugo-theme-runbook)"
TIMEOUT = 20
WORKERS = 8


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []          # (kind, url)
        self.anchors = set()     # id= and name= present on this page

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if a.get("id"):
            self.anchors.add(a["id"])
        if tag == "a" and a.get("name"):
            self.anchors.add(a["name"])

        if tag == "a" and a.get("href"):
            self.links.append(("a", a["href"]))
        elif tag == "link" and a.get("href"):
            rels = {r.lower() for r in a.get("rel", "").split()}
            # `canonical` and `alternate` point at the deployed baseURL, which does not
            # exist on disk. Checking them here would report a false failure on every page.
            if not rels & {"canonical", "alternate"}:
                self.links.append(("link", a["href"]))
        elif tag in ("img", "script", "iframe", "source", "video", "audio", "embed"):
            if a.get("src"):
                self.links.append((tag, a["src"]))


def load_exclusions(path: Path):
    if not path.is_file():
        return [], []
    data = json.loads(path.read_text(encoding="utf-8"))
    patterns, errors = [], []
    for pattern, reason in data.items():
        if pattern.startswith("_"):
            continue    # a note, not a pattern
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"exclusion {pattern!r} has no reason — every entry must carry one")
            continue
        patterns.append((re.compile(pattern), reason))
    return patterns, errors


def excluded(url, patterns):
    for pattern, reason in patterns:
        if pattern.search(url):
            return reason
    return None


def gather(build: Path, base_host: str):
    """Return (internal_problems, external_urls)."""
    pages = sorted(build.rglob("*.html"))
    anchors_by_page = {}
    parsed = {}

    for page in pages:
        p = LinkParser()
        p.feed(page.read_text(encoding="utf-8", errors="replace"))
        rel = page.relative_to(build).as_posix()
        parsed[rel] = p
        anchors_by_page[rel] = p.anchors

    problems = []
    external = {}

    for rel, p in parsed.items():
        page_dir = "/" + rel.rsplit("/", 1)[0] if "/" in rel else "/"
        for kind, raw in p.links:
            url = raw.strip()
            if not url or url.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue
            u = urlparse(url)

            if u.scheme in ("http", "https"):
                if base_host and u.netloc == base_host:
                    # Same site, written absolutely. Fold back to a path and check locally.
                    url = u.path + (f"#{u.fragment}" if u.fragment else "")
                    u = urlparse(url)
                else:
                    external.setdefault(urldefrag(url)[0], []).append(rel)
                    continue
            elif u.scheme:
                continue

            path, frag = u.path, u.fragment
            if not path:
                # Pure fragment: must exist on this page.
                if frag and frag not in anchors_by_page[rel]:
                    problems.append(f"{rel}: #{frag} — no element with that id on the page")
                continue

            target = path if path.startswith("/") else urljoin(page_dir + "/", path)
            candidate = build / target.lstrip("/")
            if candidate.is_dir():
                candidate = candidate / "index.html"
            if not candidate.is_file():
                problems.append(f"{rel}: {raw} — {target} is not in the build ({kind})")
                continue

            if frag and candidate.suffix == ".html":
                target_rel = candidate.relative_to(build).as_posix()
                known = anchors_by_page.get(target_rel)
                if known is not None and frag not in known:
                    problems.append(f"{rel}: {raw} — {target_rel} has no id={frag!r}")

    return problems, external


def probe(url):
    """HEAD, falling back to GET. Returns (url, ok, detail)."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        })
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return url, True, f"{resp.status} {method}"
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue    # plenty of hosts refuse HEAD but serve GET fine
            return url, False, f"HTTP {exc.code}"
        except Exception as exc:                            # noqa: BLE001
            if method == "HEAD":
                continue
            return url, False, type(exc).__name__ + (f": {exc}" if str(exc) else "")
    return url, False, "unreachable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_dir", type=Path)
    parser.add_argument("--external", action="store_true",
                        help="also sweep outbound URLs over the network (weekly job only)")
    parser.add_argument("--internal-only", action="store_true", default=True,
                        help=argparse.SUPPRESS)
    parser.add_argument("--base-url", default=None,
                        help="site baseURL; inferred from the homepage canonical if omitted")
    parser.add_argument("--exclusions", type=Path, default=None)
    args = parser.parse_args()

    build = args.build_dir.resolve()
    if not build.is_dir():
        print(f"FAIL: {build} is not a directory", file=sys.stderr)
        return 2

    base_host = ""
    if args.base_url:
        base_host = urlparse(args.base_url).netloc
    else:
        home = build / "index.html"
        if home.is_file():
            # Attribute values may be unquoted: `hugo --minify` strips the quotes and
            # emits `<link rel=canonical href=https://…>`. A pattern that assumes quotes
            # finds no base host on a minified build, and every same-origin absolute link
            # is then treated as external and probed over the network.
            m = re.search(
                r"""<link[^>]+rel=["']?canonical["']?[^>]+href=(?:["']([^"']+)|([^\s>"']+))""",
                home.read_text(encoding="utf-8", errors="replace"),
            )
            if m:
                base_host = urlparse(m.group(1) or m.group(2)).netloc

    exclusion_path = args.exclusions or (Path(__file__).resolve().parent.parent / DEFAULT_EXCLUSIONS)
    patterns, exclusion_errors = load_exclusions(exclusion_path)
    for err in exclusion_errors:
        print(f"  [FAIL] {err}")

    problems, external = gather(build, base_host)

    print("Internal links — resolved against the build tree, no network")
    print(f"  base host: {base_host or '(none found)'}, {len(external)} distinct external URL(s)")
    for problem in problems[:40]:
        print(f"  [FAIL] {problem}")
    if len(problems) > 40:
        print(f"  … and {len(problems) - 40} more")
    if not problems:
        print("  no broken internal links, subresources or fragments")

    failed = list(problems) + list(exclusion_errors)

    if args.external:
        print()
        print("External links — weekly sweep, never per-PR (specs/007 §3.5)")
        to_check, skipped = [], []
        for url in sorted(external):
            reason = excluded(url, patterns)
            if reason:
                skipped.append((url, reason))
            else:
                to_check.append(url)
        for url, reason in skipped:
            print(f"  [skip] {url}\n         excluded: {reason}")
        print(f"  probing {len(to_check)} URL(s) with {WORKERS} workers")
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for url, ok, detail in pool.map(probe, to_check):
                if ok:
                    continue
                pages = ", ".join(sorted(set(external[url]))[:3])
                print(f"  [FAIL] {url} — {detail}\n         linked from: {pages}")
                failed.append(f"{url} — {detail}")

    print()
    if failed:
        print(f"FAIL: {len(failed)} link problem(s)")
        return 1
    print("PASS: links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
