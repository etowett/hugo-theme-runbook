#!/usr/bin/env python3
"""JSON-LD gate — parse every ld+json block in a build and assert on its VALUES.

specs/007 §3.5. The reference site shipped double-encoded JSON-LD on **493 of 493**
article pages for months and nobody caught it, because the bug does not break parsing.
Go's ``html/template`` contextually escapes the body of a ``<script>`` block as
JavaScript and re-escapes JSON that is already valid, so interpolating per field::

    "headline": {{ .Title | jsonify }}

emits::

    "headline":"\\"How to Install Redis\\""

That is valid JSON. ``json.loads`` accepts it happily. Every structured-data linter that
only checks syntax accepts it too. The only thing that catches it is asserting on the
decoded *value* — hence the two assertions below, which are deliberately narrow and
deliberately about content rather than shape:

* ``headline`` must not begin with a quote character.
* ``datePublished`` must match ``^\\d{4}-\\d{2}-\\d{2}T`` — a double-encoded date is no
  longer a valid ISO 8601 date, so this catches the same bug from a second direction.

Generalised: any string whose value both starts and ends with a quote character has been
encoded twice, whatever key it sits under, so that is checked across the whole document.

Tolerant of an unfinished theme by design: while ``head/schema.html`` is still the
foundation stub that emits only a ``WebSite`` node, there are no ``Article`` nodes to
assert on. The script reports that as a TODO and exits 0. Pass ``--require-article``
(and flip the flag in .github/workflows/ci.yml) the day Article schema lands, so the
assertions become blocking without anyone having to remember this file exists.

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class LdJsonExtractor(HTMLParser):
    """Pull every ld+json body out of a page.

    Uses a real HTML parser rather than a regex, because Hugo's ``--minify`` strips
    attribute quotes and emits ``<script type=application/ld+json>``. A regex written
    against the quoted form matches nothing there and the gate passes by finding no
    blocks at all — silently, on exactly the production-shaped build it most needs to
    check. That is the failure mode this whole script exists to avoid, so it is not
    allowed to have it too — and finding *zero* blocks in a whole build is treated as a
    failure rather than a quiet pass, for the same reason.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._collecting = False
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        stype = a.get("type", "").strip().lower().split(";")[0]
        if stype == "application/ld+json":
            self._collecting = True
            self._buffer = []

    def handle_endtag(self, tag):
        if tag == "script" and self._collecting:
            self.blocks.append("".join(self._buffer))
            self._collecting = False
            self._buffer = []

    def handle_data(self, data):
        if self._collecting:
            self._buffer.append(data)


def extract(html: str):
    parser = LdJsonExtractor()
    parser.feed(html)
    parser.close()
    return parser.blocks

# Schema.org types that specs/004 §2a treats as an article page.
ARTICLE_TYPES = {"Article", "BlogPosting", "TechArticle", "NewsArticle", "Report"}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")

# Straight and curly quotes. A double-encoded value is wrapped in whichever quote
# character the encoder used.
QUOTES = "\"'“”‘’"


class Finding:
    def __init__(self, level, page, message, detail=""):
        self.level = level  # "FAIL" | "TODO"
        self.page = page
        self.message = message
        self.detail = detail

    def __str__(self):
        out = f"  [{self.level}] {self.page}: {self.message}"
        if self.detail:
            out += f"\n         {self.detail}"
        return out


def iter_nodes(obj):
    """Yield every dict in a JSON-LD document, flattening @graph and arrays."""
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_nodes(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_nodes(item)


def iter_strings(obj, path=""):
    """Yield (json-path, string) for every string leaf."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from iter_strings(value, f"{path}.{key}" if path else str(key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from iter_strings(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def node_types(node):
    raw = node.get("@type")
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {t for t in raw if isinstance(t, str)}
    return set()


def check_page(rel: str, html: str, findings: list) -> int:
    """Check one HTML file. Returns the number of Article nodes seen."""
    articles = 0

    for raw in extract(html):
        body = raw.strip()
        if not body:
            findings.append(Finding("FAIL", rel, "empty <script type=application/ld+json> block"))
            continue

        try:
            doc = json.loads(body)
        except json.JSONDecodeError as exc:
            findings.append(Finding(
                "FAIL", rel,
                f"ld+json does not parse: {exc}",
                body[:180] + ("…" if len(body) > 180 else ""),
            ))
            continue

        # The whole block encoded twice: json.loads returns the JSON *text*, not an object.
        if isinstance(doc, str):
            findings.append(Finding(
                "FAIL", rel,
                "the entire ld+json block is double-encoded — it decodes to a string, not an object",
                "Build one map and `jsonify | safeJS` ONCE. See specs/004 §2a.",
            ))
            continue

        if isinstance(doc, dict) and "@context" not in doc:
            findings.append(Finding("FAIL", rel, "ld+json block has no @context"))

        # Generalised double-encoding scan. A value wrapped in quotes on both ends went
        # through jsonify twice — the exact defect that survived 493 pages of review.
        for path, value in iter_strings(doc):
            if len(value) >= 2 and value[0] in QUOTES and value[-1] in QUOTES:
                findings.append(Finding(
                    "FAIL", rel,
                    f"double-encoded value at `{path}`",
                    f"decoded to {value!r} — the quotes are part of the string. specs/004 §2a.",
                ))

        for node in iter_nodes(doc):
            if not isinstance(node, dict):
                continue
            if not (node_types(node) & ARTICLE_TYPES):
                continue
            articles += 1

            headline = node.get("headline")
            if headline is None:
                findings.append(Finding("FAIL", rel, "Article node has no `headline`"))
            elif not isinstance(headline, str):
                findings.append(Finding(
                    "FAIL", rel, f"`headline` is {type(headline).__name__}, expected string"))
            elif headline[:1] in QUOTES:
                findings.append(Finding(
                    "FAIL", rel,
                    "`headline` begins with a quote character — double-encoded",
                    f"got {headline!r}",
                ))

            published = node.get("datePublished")
            if published is None:
                findings.append(Finding("FAIL", rel, "Article node has no `datePublished`"))
            elif not isinstance(published, str) or not DATE_RE.match(published):
                findings.append(Finding(
                    "FAIL", rel,
                    "`datePublished` does not match ^\\d{4}-\\d{2}-\\d{2}T",
                    f"got {published!r}",
                ))

            modified = node.get("dateModified")
            if modified is not None and (not isinstance(modified, str) or not DATE_RE.match(modified)):
                findings.append(Finding(
                    "FAIL", rel,
                    "`dateModified` does not match ^\\d{4}-\\d{2}-\\d{2}T",
                    f"got {modified!r}",
                ))

    return articles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("build_dir", type=Path, help="a built Hugo site (e.g. public/)")
    parser.add_argument(
        "--require-article",
        action="store_true",
        help="fail if the build contains no Article-typed node at all. Turn this on "
             "once head/schema.html emits Article schema (specs/004 §2a).",
    )
    args = parser.parse_args()

    build = args.build_dir.resolve()
    if not build.is_dir():
        print(f"FAIL: {build} is not a directory", file=sys.stderr)
        return 2

    pages = sorted(build.rglob("*.html"))
    if not pages:
        print(f"FAIL: no HTML files under {build}", file=sys.stderr)
        return 2

    findings: list = []
    blocks = 0
    articles = 0
    pages_with_ld = 0

    for page in pages:
        rel = page.relative_to(build).as_posix()
        html = page.read_text(encoding="utf-8", errors="replace")
        found = extract(html)
        if found:
            pages_with_ld += 1
            blocks += len(found)
        articles += check_page(rel, html, findings)

    print("JSON-LD — every ld+json block parses, and Article values are asserted")
    print(f"  {len(pages)} HTML pages, {pages_with_ld} carrying ld+json, {blocks} blocks, "
          f"{articles} Article node(s)")

    if blocks == 0:
        # Not a pass. `params.runbook.seo.jsonLd` defaults to true and
        # layouts/_partials/head/schema.html emits a node on every page, so zero blocks
        # means either the partial regressed or this script stopped finding them — and
        # the second of those is how a JSON-LD gate ends up guarding nothing at all.
        findings.append(Finding(
            "FAIL", "(build)",
            "no ld+json block anywhere in the build",
            "Expected at least one per page from head/schema.html. If this is deliberate, "
            "`params.runbook.seo.jsonLd` was turned off — say so in the PR rather than "
            "leaving the gate green and empty.",
        ))

    fails = [f for f in findings if f.level == "FAIL"]
    for finding in fails[:40]:
        print(finding)
    if len(fails) > 40:
        print(f"  … and {len(fails) - 40} more")

    if fails:
        print(f"FAIL: {len(fails)} JSON-LD problem(s)")
        return 1

    if articles == 0:
        msg = ("no Article-typed node in the build — head/schema.html is still the "
               "foundation stub emitting WebSite only (specs/004 §2a)")
        if args.require_article:
            print(f"FAIL: {msg}")
            return 1
        print(f"  TODO: {msg}.")
        print("        The headline/datePublished assertions are inert until it lands.")
        print("        Flip --require-article in .github/workflows/ci.yml at that point.")

    print("PASS: JSON-LD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
