#!/usr/bin/env python3
"""Fixture-corpus gate — assert the Layer-1 fixtures still have the properties they claim.

specs/007 §2. A fixture whose defining property has quietly drifted still builds, still
looks fine, and guards nothing. That is not hypothetical: the original fixture list in
issue #1 named seven required pages and three of them no longer existed by the time
anyone checked, which is the whole reason Layer 1 was moved into this repository. The
same rot applies inside the repository — someone reflows an 854-character line to make a
diff readable, or trims "the 158-block page" to 40 blocks while tidying, and the fixture
silently stops testing the thing it is named after.

So the properties are asserted, not trusted:

    python3 scripts/check_fixtures.py

The two large fixtures are generated rather than hand-written, and this script is also
their generator:

    python3 scripts/check_fixtures.py --regenerate

Regeneration is deterministic — no randomness, no timestamps — so re-running it on an
unchanged tree produces a zero-byte diff, and `--check-generated` proves that in CI.

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CONTENT = Path("exampleSite/content/posts")

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


class Block:
    def __init__(self, fence, info, lines, start):
        self.fence = fence            # "```" or "~~~"
        self.info = info.strip()      # e.g. 'yaml {file="x" hl_lines="3-4"}'
        self.lines = lines
        self.start = start

    @property
    def lang(self):
        return self.info.split("{")[0].strip()

    @property
    def attrs(self):
        m = re.search(r"\{(.*)\}", self.info)
        return m.group(1) if m else ""

    @property
    def longest_line(self):
        return max((len(line) for line in self.lines), default=0)


class Doc:
    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        self.blocks = []
        self.indented = []
        self._parse()

    def _parse(self):
        lines = self.text.splitlines()
        i = 0
        in_front_matter = False
        while i < len(lines):
            line = lines[i]
            if i == 0 and line.strip() == "---":
                in_front_matter = True
                i += 1
                continue
            if in_front_matter:
                if line.strip() == "---":
                    in_front_matter = False
                i += 1
                continue

            m = FENCE_RE.match(line)
            if m and m.group(1) == "":
                marker, info = m.group(2), m.group(3)
                body = []
                i += 1
                while i < len(lines):
                    close = FENCE_RE.match(lines[i])
                    if close and close.group(2)[0] == marker[0] and len(close.group(2)) >= len(marker) \
                            and not close.group(3).strip():
                        break
                    body.append(lines[i])
                    i += 1
                self.blocks.append(Block(marker[:3], info, body, i))
                i += 1
                continue

            # A 4-space indented block, which bypasses the render hook entirely (REQ-CB-8).
            if line.startswith("    ") and line.strip() and (i == 0 or not lines[i - 1].strip()):
                run = []
                while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                    run.append(lines[i])
                    i += 1
                if any(r.strip() for r in run):
                    self.indented.append(run)
                continue
            i += 1

    def has_attr(self, key):
        return any(re.search(rf"\b{re.escape(key)}\s*=", b.attrs) for b in self.blocks)


# ── Invariants ────────────────────────────────────────────────────────────────────────
# (fixture filename, [(what it guards, predicate)]). Every row here maps to a row in the
# specs/007 §2 Layer 1 table.
CHECKS = [
    ("code-block-smoke-test.md", [
        ("REQ-CB-2 one-line block",
         lambda d: any(len(b.lines) == 1 for b in d.blocks)),
        ("REQ-CB-2 two-line block",
         lambda d: any(len(b.lines) == 2 for b in d.blocks)),
        ("REQ-CB-2 three-line block",
         lambda d: any(len(b.lines) == 3 for b in d.blocks)),
        ("hook fires with an empty .Type (untagged backtick fence)",
         lambda d: any(b.fence == "```" and b.lang == "" for b in d.blocks)),
        ("hook fires on a tilde fence",
         lambda d: any(b.fence == "~~~" for b in d.blocks)),
        ("lexer fallback: an unknown language tag",
         lambda d: any(b.lang == "frobnicate-9000" for b in d.blocks)),
        ("REQ-CB-1 per-block line-number opt-in",
         lambda d: d.has_attr("linenos")),
        ("REQ-CB-7 attribute routing: file=",
         lambda d: d.has_attr("file")),
        ("REQ-CB-7 attribute routing: hl_lines=",
         lambda d: d.has_attr("hl_lines")),
        ("Q2 copy semantics: prompt=",
         lambda d: d.has_attr("prompt")),
        ("Q3 output treatment: output=",
         lambda d: d.has_attr("output")),
        ("REQ-CB-5 the corpus-maximum 854-character line, exactly",
         lambda d: any(b.longest_line == 854 for b in d.blocks)),
        ("REQ-FONT-1 box-drawing glyphs in shell output",
         lambda d: all(g in d.text for g in "└├─●")),
        ("REQ-CB-8 a 4-space indented block that bypasses the hook",
         lambda d: len(d.indented) >= 1),
        ("inline code spans in prose",
         lambda d: len(re.findall(r"(?<!`)`[^`\n]+`(?!`)", d.text)) >= 5),
        ("no malformed fence is preserved (specs/007 §2)",
         lambda d: d.text.count("```") % 2 == 0),
    ]),
    ("code-blocks-158.md", [
        ("per-block JS and CSS cost at the corpus maximum: exactly 158 blocks",
         lambda d: len(d.blocks) == 158),
    ]),
    ("code-block-767-lines.md", [
        ("long-block rendering: one block of exactly 767 lines",
         lambda d: any(len(b.lines) == 767 for b in d.blocks)),
        ("it is the only block on the page, so the measurement is unambiguous",
         lambda d: len(d.blocks) == 1),
        # Verified against a real build: an UNKNOWN lexer makes Hugo emit a bare
        # <pre><code> with no div.highlight, no pre.chroma and no span.line wrappers at
        # all. `conf` is one such tag. Tagged with it, this fixture would measure the
        # cost of NOT highlighting 767 lines, which is not what it is for.
        ("it uses a Chroma-known lexer, so it measures highlighting at scale",
         lambda d: d.blocks[0].lang in {"ini", "yaml", "toml", "sh", "bash", "nginx"}),
    ]),
    ("theme-shell-baseline.md", [
        ("specs/005 §3.1 synthetic fixture stays minimal: at most one code block",
         lambda d: len(d.blocks) <= 1),
        ("and stays short, or it stops measuring the theme shell",
         lambda d: len(d.text) < 1600),
    ]),
    ("tables-and-data.md", [
        ("layout: at least one table",
         lambda d: d.text.count("\n|") >= 8),
        ("layout: a table wider than a phone viewport",
         lambda d: any(len(line) > 140 for line in d.text.splitlines() if line.startswith("|"))),
        ("layout: nested lists",
         lambda d: re.search(r"^\s{2,}[-*] ", d.text, re.MULTILINE) is not None),
    ]),
    ("admonitions-and-callouts.md", [
        ("shortcodes: GitHub alert blockquotes",
         lambda d: len(re.findall(r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]",
                                  d.text, re.MULTILINE)) >= 5),
        ("a plain blockquote alerts must not swallow",
         lambda d: re.search(r"^> [^\[]", d.text, re.MULTILINE) is not None),
        # This invariant was the exact inverse until the shortcodes landed: it asserted
        # NO shortcode call, because layouts/shortcodes/ was empty and calling a
        # shortcode that does not exist is a hard build failure. Correct then, wrong the
        # moment admonition.html and details.html shipped — and the guard caught the
        # flip rather than letting the fixture quietly stop covering anything.
        #
        # The alert-blockquote assertions above stay. They are not redundant: alerts are
        # what a third-party author actually writes, having copied them from GitHub, and
        # they must keep degrading to a readable blockquote.
        ("shortcodes: admonition invoked, both named and positional",
         lambda d: len(re.findall(r"\{\{<\s*admonition\b", d.text)) >= 2),
        ("shortcodes: details invoked, with a fenced block inside it",
         lambda d: re.search(r"\{\{<\s*details\b[\s\S]*?```[\s\S]*?\{\{<\s*/\s*details\s*>\}\}",
                             d.text) is not None),
        ("an unknown admonition type, which must degrade to note rather than to nothing",
         lambda d: re.search(r'\{\{<\s*admonition\s+type="nonsense"', d.text) is not None),
    ]),
    ("tilde-fenced-post.md", [
        # The card plate finds a post's FIRST fence. Every other fixture opens with a
        # backtick one, which is how a plate that only knew ``` shipped: valid
        # CommonMark, no error, just a card that quietly lost its picture. This fixture
        # exists to be the one post that opens with a tilde, so that property is the
        # thing asserted — not the presence of a tilde somewhere in the file.
        ("the FIRST fence is a tilde fence",
         lambda d: re.search(r"\A(?:---.*?---\s*)?(?:[^`~]|`(?!``)|~(?!~~))*~~~", d.text, re.S) is not None),
        ("a backtick fence follows it, so the two patterns cannot be conflated",
         lambda d: "```yaml" in d.text),
    ]),
    ("tabs-and-variant-procedures.md", [
        # Registered late: an unregistered fixture is silently skipped by this script,
        # so the file existed while nothing checked it still did its job.
        ("tabs: the shortcode is invoked",
         lambda d: len(re.findall(r"\{\{<\s*tabs\b", d.text)) >= 1),
        ("tabs: more than one panel, or it is not exercising anything",
         lambda d: len(re.findall(r"\{\{<\s*tab\b", d.text)) >= 2),
        ("a fenced block inside a panel, which must still reach the code hook",
         lambda d: re.search(r"\{\{<\s*tab\b[\s\S]*?```", d.text) is not None),
    ]),
    ("prose-only-no-code.md", [
        ("the no-code case: zero fenced blocks",
         lambda d: len(d.blocks) == 0),
        ("and zero indented blocks",
         lambda d: len(d.indented) == 0),
        ("long enough to exercise prose measure and reading time",
         lambda d: len(d.text.split()) >= 400),
    ]),
    ("rtl-bidirectional-text.md", [
        ("i18n: Arabic prose present",
         lambda d: re.search(r"[؀-ۿ]", d.text) is not None),
        ("i18n: LTR code blocks inside RTL prose",
         lambda d: len(d.blocks) >= 2),
        ("i18n: a mixed-direction table",
         lambda d: "|" in d.text and re.search(r"\|[^|\n]*[؀-ۿ]", d.text) is not None),
    ]),
]


# ── Generators ────────────────────────────────────────────────────────────────────────

def gen_158_blocks() -> str:
    """The maximum-block page: 158 fenced blocks on one URL.

    The reference corpus maximum is 158 blocks in a single post. At 18.2 blocks per post
    on average this is the tail case that decides whether per-block JavaScript is
    affordable: a copy button wired with 158 individual listeners, 158 clipboard
    closures and 158 ResizeObservers behaves very differently from one delegated
    listener on the article. It is also the page that shows whether per-block CSS is
    doing layout work it does not need to.
    """
    steps = [
        ("sh", ["sudo dnf -y install {pkg}"]),
        ("sh", ["sudo systemctl enable --now {pkg}", "sudo systemctl status {pkg}"]),
        ("sh", ["sudo firewall-cmd --permanent --add-port={port}/tcp",
                "sudo firewall-cmd --reload"]),
        ("yaml", ["service:", "  name: {pkg}", "  port: {port}", "  enabled: true"]),
        ("text", ["● {pkg}.service - {Pkg} daemon",
                  "     Loaded: loaded (/usr/lib/systemd/system/{pkg}.service; enabled)",
                  "     Active: active (running)",
                  "     CGroup: /system.slice/{pkg}.service",
                  "             └─{pid} /usr/sbin/{pkg}"]),
        ("sh", ["curl -fsSL http://127.0.0.1:{port}/healthz"]),
        ("ini", ["[{pkg}]", "bind = 127.0.0.1", "port = {port}"]),
        ("json", ['{{"service": "{pkg}", "port": {port}, "healthy": true}}']),
    ]
    packages = ["redis", "nginx", "postgresql", "haproxy", "prometheus", "grafana",
                "vault", "consul", "etcd", "containerd", "chrony", "rsyslog",
                "fail2ban", "keepalived", "memcached", "rabbitmq", "elasticsearch",
                "influxdb", "telegraf", "node-exporter"]

    out = [
        "---",
        'title: "Building the whole stack: 158 code blocks on one page"',
        "date: 2026-07-25",
        'description: "The maximum-block fixture — the reference corpus tops out at 158 blocks in a single post."',
        'tags: ["fixtures", "code"]',
        'categories: ["Meta"]',
        "---",
        "",
        "**Generated fixture — do not hand-edit.** Regenerate with",
        "`python3 scripts/check_fixtures.py --regenerate`.",
        "",
        "The reference corpus tops out at **158 fenced blocks in a single post**, against an average",
        "of 18.2. This page reproduces that maximum, because the tail is where per-block cost stops",
        "being theoretical: 158 individual copy-button listeners, 158 clipboard closures and 158",
        "`ResizeObserver`s behave nothing like one delegated listener on the article element, and the",
        "difference does not show up on a page with four blocks.",
        "",
        "It is also the page-weight worst case for markup that scales with block count, and the",
        "fixture the visual-regression suite should screenshot at 360 px to check that block chrome",
        "does not accumulate vertical drift.",
        "",
    ]

    count = 0
    section = 0
    while count < 158:
        pkg = packages[section % len(packages)]
        section += 1
        out.append(f"## Step {section} — {pkg}")
        out.append("")
        out.append(f"Install, enable and verify `{pkg}`.")
        out.append("")
        for lang, body in steps:
            if count >= 158:
                break
            count += 1
            port = 6000 + count
            pid = 1000 + count * 7
            out.append(f"```{lang}")
            for line in body:
                out.append(line.format(pkg=pkg, Pkg=pkg.capitalize(), port=port, pid=pid))
            out.append("```")
            out.append("")

    out.append(f"That is {count} blocks.")
    out.append("")
    return "\n".join(out)


def gen_767_line_block() -> str:
    """The long-block page: one fence of exactly 767 lines.

    The corpus maximum single block is 767 lines. It matters for three reasons that only
    appear at that length: whether the copy button stays reachable when the block is
    taller than the viewport (REQ-CB-3), whether a line-number gutter — if a consuming
    site forces one on, which REQ-CB-1 exists to prevent — stays aligned over three
    digits of line number, and whether syntax highlighting of that many lines shows up
    in build time or page weight.
    """
    header = [
        "# redis.conf — generated fixture, 767 lines exactly.",
        "# Regenerate with: python3 scripts/check_fixtures.py --regenerate",
        "#",
        "# The reference corpus maximum for a single fenced block is 767 lines. A block this",
        "# long is where the copy button scrolls out of reach, where a forced line-number",
        "# gutter changes width at line 100, and where highlighting cost becomes visible.",
        "",
        "################################## NETWORK #####################################",
        "",
        "bind 127.0.0.1 -::1",
        "protected-mode yes",
        "port 6379",
        "tcp-backlog 511",
        "timeout 0",
        "tcp-keepalive 300",
        "",
    ]

    sections = [
        ("GENERAL", [
            ("daemonize", "no", "Run as a foreground process; systemd supervises it."),
            ("supervised", "systemd", "Signal readiness to the service manager."),
            ("pidfile", "/run/redis/redis-server.pid", "Written before privileges drop."),
            ("loglevel", "notice", "debug | verbose | notice | warning"),
            ("logfile", "/var/log/redis/redis-server.log", "Empty string logs to stdout."),
            ("databases", "16", "Logical databases, selected with SELECT."),
        ]),
        ("SNAPSHOTTING", [
            ("save", "900 1", "One change in fifteen minutes."),
            ("save", "300 10", "Ten changes in five minutes."),
            ("save", "60 10000", "Ten thousand changes in one minute."),
            ("stop-writes-on-bgsave-error", "yes", "Fail loudly rather than losing data quietly."),
            ("rdbcompression", "yes", "LZF on string values inside the dump."),
            ("rdbchecksum", "yes", "CRC64 at the end of the file."),
            ("dbfilename", "dump.rdb", "Relative to dir below."),
            ("dir", "/var/lib/redis", "Working directory for the dump and the AOF."),
        ]),
        ("REPLICATION", [
            ("replica-serve-stale-data", "yes", "Serve reads during a link outage."),
            ("replica-read-only", "yes", "Writes to a replica are refused."),
            ("repl-diskless-sync", "yes", "Stream the RDB rather than staging it on disk."),
            ("repl-diskless-sync-delay", "5", "Wait to batch arriving replicas."),
            ("repl-disable-tcp-nodelay", "no", "Latency over bandwidth."),
            ("replica-priority", "100", "Lower wins a failover election."),
        ]),
        ("SECURITY", [
            ("acllog-max-len", "128", "Retained ACL security events."),
            ("requirepass", "CHANGE_ME_IN_PRODUCTION", "Placeholder; never a real credential."),
        ]),
        ("CLIENTS", [
            ("maxclients", "10000", "Bounded by the file-descriptor limit."),
        ]),
        ("MEMORY MANAGEMENT", [
            ("maxmemory", "256mb", "Size to the box, not to the default."),
            ("maxmemory-policy", "allkeys-lru", "Cache workload; use noeviction for a store."),
            ("maxmemory-samples", "5", "Approximation quality for LRU and LFU."),
            ("replica-ignore-maxmemory", "yes", "Eviction is driven by the primary."),
        ]),
        ("LAZY FREEING", [
            ("lazyfree-lazy-eviction", "no", ""),
            ("lazyfree-lazy-expire", "no", ""),
            ("lazyfree-lazy-server-del", "no", ""),
            ("replica-lazy-flush", "no", ""),
            ("lazyfree-lazy-user-del", "no", ""),
            ("lazyfree-lazy-user-flush", "no", ""),
        ]),
        ("APPEND ONLY MODE", [
            ("appendonly", "yes", "Durability beyond the RDB snapshot interval."),
            ("appendfilename", '"appendonly.aof"', ""),
            ("appenddirname", '"appendonlydir"', ""),
            ("appendfsync", "everysec", "always | everysec | no"),
            ("no-appendfsync-on-rewrite", "no", ""),
            ("auto-aof-rewrite-percentage", "100", ""),
            ("auto-aof-rewrite-min-size", "64mb", ""),
            ("aof-load-truncated", "yes", ""),
            ("aof-use-rdb-preamble", "yes", ""),
            ("aof-timestamp-enabled", "no", ""),
        ]),
        ("SLOW LOG", [
            ("slowlog-log-slower-than", "10000", "Microseconds."),
            ("slowlog-max-len", "128", ""),
        ]),
        ("LATENCY MONITOR", [
            ("latency-monitor-threshold", "0", "Zero disables the monitor."),
            ("latency-tracking", "yes", ""),
            ("latency-tracking-info-percentiles", "50 99 99.9", ""),
        ]),
        ("EVENT NOTIFICATION", [
            ("notify-keyspace-events", '""', "Costs CPU; enable only what is consumed."),
        ]),
        ("ADVANCED CONFIG", [
            ("hash-max-listpack-entries", "128", ""),
            ("hash-max-listpack-value", "64", ""),
            ("list-max-listpack-size", "-2", ""),
            ("list-compress-depth", "0", ""),
            ("set-max-intset-entries", "512", ""),
            ("set-max-listpack-entries", "128", ""),
            ("set-max-listpack-value", "64", ""),
            ("zset-max-listpack-entries", "128", ""),
            ("zset-max-listpack-value", "64", ""),
            ("hll-sparse-max-bytes", "3000", ""),
            ("stream-node-max-bytes", "4096", ""),
            ("stream-node-max-entries", "100", ""),
            ("activerehashing", "yes", ""),
            ("client-output-buffer-limit", "normal 0 0 0", ""),
            ("client-output-buffer-limit", "replica 256mb 64mb 60", ""),
            ("client-output-buffer-limit", "pubsub 32mb 8mb 60", ""),
            ("hz", "10", ""),
            ("dynamic-hz", "yes", ""),
            ("aof-rewrite-incremental-fsync", "yes", ""),
            ("rdb-save-incremental-fsync", "yes", ""),
            ("jemalloc-bg-thread", "yes", ""),
        ]),
    ]

    body = list(header)
    # Cycle the sections until the block is long enough, renaming each repeat so the file
    # reads like a real long config rather than a copy-paste loop.
    repeat = 0
    while len(body) < 767:
        for name, entries in sections:
            if len(body) >= 767:
                break
            suffix = "" if repeat == 0 else f" (instance {repeat + 1})"
            bar = "#" * max(4, (80 - len(name) - len(suffix) - 2) // 2)
            body.append(f"{bar} {name}{suffix} {bar}")
            body.append("")
            for key, value, comment in entries:
                if len(body) >= 767:
                    break
                if comment:
                    body.append(f"# {comment}")
                prefix = "" if repeat == 0 else f"instance{repeat + 1}-"
                body.append(f"{prefix}{key} {value}")
                body.append("")
        repeat += 1

    body = body[:767]
    # Never end on a dangling comment: the last line should be a directive.
    if body[-1].startswith("#") or not body[-1].strip():
        body[-1] = "activerehashing yes"

    assert len(body) == 767, len(body)

    out = [
        "---",
        'title: "A 767-line redis.conf"',
        "date: 2026-07-26",
        'description: "The long-block fixture — one fenced block of exactly 767 lines, the corpus maximum."',
        'tags: ["fixtures", "code"]',
        'categories: ["Meta"]',
        "---",
        "",
        "**Generated fixture — do not hand-edit.** Regenerate with",
        "`python3 scripts/check_fixtures.py --regenerate`.",
        "",
        "One fenced block, **exactly 767 lines** — the longest single block in the reference corpus.",
        "Three things only go wrong at this length: the copy button scrolls out of reach when the",
        "block is taller than the viewport (REQ-CB-3), a line-number gutter changes width at line 100",
        "and again at line 1000 and pushes the code sideways mid-block, and syntax highlighting of",
        "this many lines starts to show up in build time and page weight.",
        "",
        "Nothing else is on this page, so anything measured here is attributable to the block.",
        "",
        "The language tag is `ini`, which Chroma has a lexer for, deliberately. An unknown tag makes",
        "Hugo emit a bare `<pre><code>` with no `div.highlight`, no `pre.chroma` and no",
        "`span.line` wrappers at all — see the unsupported-language case on the smoke-test page — so a",
        "767-line block tagged with one would measure the cost of *not* highlighting.",
        "",
        "```ini",
    ]
    out += body
    out += ["```", ""]
    return "\n".join(out)


GENERATED = {
    "code-blocks-158.md": gen_158_blocks,
    "code-block-767-lines.md": gen_767_line_block,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--regenerate", action="store_true",
                        help="rewrite the generated fixtures from their generators")
    parser.add_argument("--check-generated", action="store_true",
                        help="fail if regeneration would change anything (for CI)")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    content = root / CONTENT
    if not content.is_dir():
        print(f"FAIL: {content} does not exist", file=sys.stderr)
        return 2

    if args.regenerate:
        for name, gen in GENERATED.items():
            (content / name).write_text(gen(), encoding="utf-8")
            print(f"  wrote {(content / name).relative_to(root)}")
        print("PASS: fixtures regenerated")
        return 0

    print("Fixture corpus — specs/007 §2 Layer 1")
    failures = []

    if args.check_generated:
        for name, gen in GENERATED.items():
            path = content / name
            expected = gen()
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != expected:
                failures.append(
                    f"{name} is out of sync with its generator — run "
                    f"`python3 scripts/check_fixtures.py --regenerate`"
                )
            else:
                print(f"  [ok  ] {name} matches its generator byte for byte")

    for name, checks in CHECKS:
        path = content / name
        if not path.is_file():
            failures.append(f"{name} is missing from {CONTENT}")
            print(f"  [FAIL] {name}: missing")
            continue
        doc = Doc(path)
        print(f"  {name} — {len(doc.blocks)} fenced block(s), "
              f"{len(doc.indented)} indented block(s)")
        for label, predicate in checks:
            try:
                ok = bool(predicate(doc))
            except Exception as exc:                       # noqa: BLE001
                ok, label = False, f"{label} (predicate raised {exc!r})"
            print(f"    [{'ok  ' if ok else 'FAIL'}] {label}")
            if not ok:
                failures.append(f"{name}: {label}")

    print()
    if failures:
        print(f"FAIL: {len(failures)} fixture invariant(s) broken")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS: fixtures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
