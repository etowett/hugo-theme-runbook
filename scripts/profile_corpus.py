#!/usr/bin/env python3
"""Fence-aware profiler for a Hugo content archive.

Produces the measurements in specs/002-corpus-profile.md. Every design decision
in these specs is derived from a real archive rather than from taste, which only
works if the numbers are current -- and they have already gone stale twice while
the reference site was being cleaned up. Run this instead of trusting the doc.

Naive grep miscounts this kind of corpus badly in both directions: shell "#"
comments look like Markdown headings, `image:` keys inside Kubernetes YAML look
like front matter, and code *about* HTML looks like raw HTML. This tracks fences
with CommonMark marker-length semantics and applies every metric to the correct
partition.

Stdlib only, no third-party dependencies.

Usage:
    python3 scripts/profile_corpus.py --dir ../citizix/content/post
    python3 scripts/profile_corpus.py --dir ../citizix/content/post > corpus.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path


FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
FM_DELIM = "---"


def split_front_matter(text: str) -> tuple[str, str]:
    if not text.startswith(FM_DELIM):
        return "", text
    end = text.find("\n" + FM_DELIM, len(FM_DELIM))
    if end == -1:
        return "", text
    fm = text[len(FM_DELIM) : end]
    body = text[end + len(FM_DELIM) + 1 :]
    return fm, body


def parse_fm_keys(fm: str) -> dict[str, str]:
    """Crude top-level YAML key scan — enough for coverage counting."""
    out: dict[str, str] = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def walk(body: str):
    """Yield (kind, line) where kind is 'code' or 'prose'.

    Tracks fence open/close with matching marker length, the way CommonMark does.
    """
    in_fence = False
    marker = ""
    indent = 0
    lang = None
    block: list[str] = []
    blocks: list[tuple[str | None, list[str]]] = []
    prose: list[str] = []
    unbalanced = False

    for line in body.splitlines():
        m = FENCE_RE.match(line)
        if not in_fence:
            if m and m.group(3).strip() != "" or (m and m.group(3).strip() == ""):
                # opening fence
                indent = len(m.group(1))
                marker = m.group(2)
                info = m.group(3).strip()
                lang = info.split()[0].lower().strip("{}") if info else None
                if lang:
                    lang = re.sub(r"[^a-z0-9+#._-]", "", lang)
                in_fence = True
                block = []
                continue
            prose.append(line)
        else:
            # closing fence: same char, >= length, no info string
            if m and m.group(2)[0] == marker[0] and len(m.group(2)) >= len(marker) and m.group(3).strip() == "":
                blocks.append((lang or None, block))
                in_fence = False
                lang = None
                continue
            block.append(line)

    if in_fence:
        unbalanced = True
        blocks.append((lang or None, block))

    return blocks, prose, unbalanced


INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)")
TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
INDENTED_CODE_RE = re.compile(r"^(?: {4,}|\t)\S")
RAW_PRE_RE = re.compile(r"<pre\b", re.I)
RAW_A_RE = re.compile(r"<a\s+[^>]*href=", re.I)
WP_CLASS_RE = re.compile(r"wp-block-[a-z-]+")
WP_ATTR_RE = re.compile(r"\{\.wp-block-[a-z-]+")
ENTITY_RE = re.compile(r"&(?:#x?[0-9A-Fa-f]+|[a-zA-Z][a-zA-Z0-9]{1,31});")
NBSP_RE = re.compile(r"&(?:nbsp|#160|#xA0|#x200A|#8202);", re.I)
HTML_TAG_RE = re.compile(
    r"</?(?:div|span|p|figure|figcaption|table|thead|tbody|tr|td|th|ul|ol|li|"
    r"strong|em|br|hr|img|h[1-6]|blockquote|code|iframe)\b[^>]*>",
    re.I,
)
BODY_H1_RE = re.compile(r"^#\s+\S|<h1\b", re.I)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default="content/post",
                    help="directory of Markdown posts (default: content/post)")
    args = ap.parse_args()
    posts = Path(args.dir)
    if not posts.is_dir():
        print(f"error: no such directory: {posts}", file=sys.stderr)
        return 2
    files = sorted(posts.glob("*.md"))
    if not files:
        print(f"error: no .md files in {posts}", file=sys.stderr)
        return 2
    n = len(files)

    stats: dict = {
        "posts": n,
        "blocks_total": 0,
        "blocks_by_lang": Counter(),
        "block_lines": [],
        "code_lines_over_80": 0,
        "max_code_line": 0,
        "max_code_line_file": "",
        "inline_code_spans": 0,
        "md_images": 0,
        "posts_with_image_fm": 0,
        "words": [],
        "headings": Counter(),
        "posts_with_tables": 0,
        "internal_links": 0,
        "external_links": 0,
        "categories": Counter(),
        "tags": Counter(),
        "fm_coverage": Counter(),
        "drafts": 0,
        # legacy
        "legacy_raw_pre": 0,
        "legacy_raw_pre_posts": set(),
        "legacy_raw_a": 0,
        "legacy_wp_class": 0,
        "legacy_wp_class_posts": set(),
        "legacy_wp_attr": 0,
        "legacy_indented_blocks": 0,
        "legacy_indented_posts": set(),
        "legacy_entities_in_code": 0,
        "legacy_entities_in_code_posts": set(),
        "legacy_nbsp_prose": 0,
        "legacy_nbsp_posts": set(),
        "legacy_html_tags_prose": 0,
        "legacy_html_tags_posts": set(),
        "legacy_body_h1": 0,
        "legacy_body_h1_posts": set(),
        "legacy_ocean_fm": 0,
        "unbalanced_fences": [],
        "blocks_no_lang": 0,
        "posts_with_no_code": 0,
        "blocks_per_post": [],
    }

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        fm_raw, body = split_front_matter(text)
        fm = parse_fm_keys(fm_raw)

        for key in ("title", "description", "date", "url", "keywords", "lastmod", "image", "author", "type"):
            if key in fm:
                stats["fm_coverage"][key] += 1
        if "categories" in fm_raw:
            stats["fm_coverage"]["categories"] += 1
        if "tags" in fm_raw:
            stats["fm_coverage"]["tags"] += 1
        if fm.get("draft", "").lower() == "true":
            stats["drafts"] += 1
        if "image" in fm:
            stats["posts_with_image_fm"] += 1
        if re.search(r"^ocean_", fm_raw, re.M):
            stats["legacy_ocean_fm"] += len(re.findall(r"^ocean_", fm_raw, re.M))

        # taxonomy (list form under categories:/tags:)
        for taxo in ("categories", "tags"):
            m = re.search(rf"^{taxo}:\s*\n((?:\s*-\s+.*\n)+)", fm_raw + "\n", re.M)
            if m:
                for item in re.findall(r"^\s*-\s+(.*)$", m.group(1), re.M):
                    stats[taxo][item.strip().strip("\"'")] += 1

        blocks, prose_lines, unbalanced = walk(body)
        if unbalanced:
            stats["unbalanced_fences"].append(f.name)

        stats["blocks_total"] += len(blocks)
        stats["blocks_per_post"].append(len(blocks))
        if not blocks:
            stats["posts_with_no_code"] += 1

        for lang, lines in blocks:
            stats["blocks_by_lang"][lang or "(none)"] += 1
            if lang is None:
                stats["blocks_no_lang"] += 1
            stats["block_lines"].append(len(lines))
            for cl in lines:
                if len(cl) > 80:
                    stats["code_lines_over_80"] += 1
                if len(cl) > stats["max_code_line"]:
                    stats["max_code_line"] = len(cl)
                    stats["max_code_line_file"] = f.name
                ents = ENTITY_RE.findall(cl)
                if ents:
                    stats["legacy_entities_in_code"] += len(ents)
                    stats["legacy_entities_in_code_posts"].add(f.name)

        prose = "\n".join(prose_lines)

        stats["inline_code_spans"] += len(INLINE_CODE_RE.findall(prose))
        stats["md_images"] += len(MD_IMAGE_RE.findall(prose))
        stats["words"].append(len(re.findall(r"\b[\w'-]+\b", prose)))

        has_table = False
        in_indented = False
        prev_blank = True
        for line in prose_lines:
            hm = HEADING_RE.match(line)
            if hm:
                stats["headings"][len(hm.group(1))] += 1
            if TABLE_RE.match(line):
                has_table = True
            # 4-space indented code: starts after a blank line, not inside a list
            if INDENTED_CODE_RE.match(line):
                if prev_blank and not in_indented:
                    stats["legacy_indented_blocks"] += 1
                    stats["legacy_indented_posts"].add(f.name)
                    in_indented = True
            elif line.strip() == "":
                pass
            else:
                in_indented = False
            prev_blank = line.strip() == ""

        if has_table:
            stats["posts_with_tables"] += 1

        for href in LINK_RE.findall(prose):
            if href.startswith(("http://", "https://", "//")) and "citizix.com" not in href:
                stats["external_links"] += 1
            else:
                stats["internal_links"] += 1

        # legacy scans over prose only (code fences legitimately contain HTML)
        rp = RAW_PRE_RE.findall(prose)
        if rp:
            stats["legacy_raw_pre"] += len(rp)
            stats["legacy_raw_pre_posts"].add(f.name)
        stats["legacy_raw_a"] += len(RAW_A_RE.findall(prose))
        wc = WP_CLASS_RE.findall(prose)
        if wc:
            stats["legacy_wp_class"] += len(wc)
            stats["legacy_wp_class_posts"].add(f.name)
        stats["legacy_wp_attr"] += len(WP_ATTR_RE.findall(prose))
        nb = NBSP_RE.findall(prose)
        if nb:
            stats["legacy_nbsp_prose"] += len(nb)
            stats["legacy_nbsp_posts"].add(f.name)
        ht = HTML_TAG_RE.findall(prose)
        if ht:
            stats["legacy_html_tags_prose"] += len(ht)
            stats["legacy_html_tags_posts"].add(f.name)
        h1 = [l for l in prose_lines if BODY_H1_RE.match(l)]
        if h1:
            stats["legacy_body_h1"] += len(h1)
            stats["legacy_body_h1_posts"].add(f.name)

    bl = sorted(stats["block_lines"])

    def pct(data, p):
        if not data:
            return 0
        k = max(0, min(len(data) - 1, int(round((p / 100) * len(data) + 0.5)) - 1))
        return data[k]

    words = sorted(stats["words"])
    bpp = sorted(stats["blocks_per_post"])

    shell_langs = {"sh", "bash", "shell", "zsh", "console", "shell-session"}
    shell_total = sum(v for k, v in stats["blocks_by_lang"].items() if k in shell_langs)

    out = {
        "posts": n,
        "drafts": stats["drafts"],
        "code": {
            "blocks_total": stats["blocks_total"],
            "blocks_no_lang": stats["blocks_no_lang"],
            "posts_with_no_code": stats["posts_with_no_code"],
            "mean_blocks_per_post": round(stats["blocks_total"] / n, 2),
            "blocks_per_post_median": pct(bpp, 50),
            "blocks_per_post_p75": pct(bpp, 75),
            "blocks_per_post_p90": pct(bpp, 90),
            "blocks_per_post_p99": pct(bpp, 99),
            "blocks_per_post_max": bpp[-1] if bpp else 0,
            "distinct_languages": len(stats["blocks_by_lang"]),
            "shell_family_blocks": shell_total,
            "shell_family_pct": round(100 * shell_total / max(1, stats["blocks_total"]), 1),
            "top_languages": stats["blocks_by_lang"].most_common(25),
            "block_len_median": pct(bl, 50),
            "block_len_p75": pct(bl, 75),
            "block_len_p90": pct(bl, 90),
            "block_len_p99": pct(bl, 99),
            "block_len_max": bl[-1] if bl else 0,
            "blocks_le_1_line": sum(1 for x in bl if x <= 1),
            "blocks_le_2_lines": sum(1 for x in bl if x <= 2),
            "blocks_le_3_lines": sum(1 for x in bl if x <= 3),
            "blocks_gt_30_lines": sum(1 for x in bl if x > 30),
            "code_lines_over_80": stats["code_lines_over_80"],
            "max_code_line": stats["max_code_line"],
            "max_code_line_file": stats["max_code_line_file"],
            "inline_code_spans": stats["inline_code_spans"],
            "inline_per_post": round(stats["inline_code_spans"] / n, 1),
        },
        "prose": {
            "words_mean": round(statistics.mean(words)) if words else 0,
            "words_median": pct(words, 50),
            "words_p75": pct(words, 75),
            "words_p90": pct(words, 90),
            "words_max": words[-1] if words else 0,
            "headings": dict(sorted(stats["headings"].items())),
            "posts_with_tables": stats["posts_with_tables"],
            "internal_links": stats["internal_links"],
            "internal_links_per_post": round(stats["internal_links"] / n, 2),
            "external_links": stats["external_links"],
            "md_images": stats["md_images"],
            "posts_with_image_fm": stats["posts_with_image_fm"],
        },
        "taxonomy": {
            "distinct_categories": len(stats["categories"]),
            "distinct_tags": len(stats["tags"]),
            "categories": stats["categories"].most_common(),
            "top_tags": stats["tags"].most_common(20),
            "tags_used_once": sum(1 for _, v in stats["tags"].items() if v == 1),
        },
        "front_matter_coverage": {
            k: {"count": v, "pct": round(100 * v / n, 1)}
            for k, v in sorted(stats["fm_coverage"].items())
        },
        "legacy": {
            "raw_pre_tags": stats["legacy_raw_pre"],
            "raw_pre_posts": len(stats["legacy_raw_pre_posts"]),
            "raw_a_tags": stats["legacy_raw_a"],
            "wp_block_classes": stats["legacy_wp_class"],
            "wp_block_posts": len(stats["legacy_wp_class_posts"]),
            "wp_block_heading_attrs": stats["legacy_wp_attr"],
            "indented_code_blocks": stats["legacy_indented_blocks"],
            "indented_code_posts": len(stats["legacy_indented_posts"]),
            "entities_inside_fences": stats["legacy_entities_in_code"],
            "entities_inside_fences_posts": len(stats["legacy_entities_in_code_posts"]),
            "nbsp_in_prose": stats["legacy_nbsp_prose"],
            "nbsp_posts": len(stats["legacy_nbsp_posts"]),
            "html_tags_in_prose": stats["legacy_html_tags_prose"],
            "html_tags_posts": sorted(stats["legacy_html_tags_posts"])[:20],
            "html_tags_post_count": len(stats["legacy_html_tags_posts"]),
            "body_h1": stats["legacy_body_h1"],
            "body_h1_posts": sorted(stats["legacy_body_h1_posts"])[:20],
            "body_h1_post_count": len(stats["legacy_body_h1_posts"]),
            "ocean_front_matter": stats["legacy_ocean_fm"],
            "unbalanced_fences": stats["unbalanced_fences"],
        },
    }

    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
