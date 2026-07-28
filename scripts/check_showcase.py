#!/usr/bin/env python3
"""Hugo Themes showcase compliance — specs/009 §2, checked mechanically.

The submission process changed and the old checklist is stale: `gohugoio/hugoThemes` is
archived, `reviewTheme.sh` is gone, and submission is now a **pull request** to
`gohugoio/hugoThemesSiteBuilder` adding the theme URL to `themes.txt` in lexicographical
order, gated by the Netlify deploy preview. specs/009 §1 has the full diff against what
issue #1 §5 claimed.

Findings are graded, because most of this cannot be fixed yet:

    FAIL  a real violation of a rule the repo already claims to meet
    TODO  a requirement whose artefact does not exist yet (screenshots, the demo site)
    NOTE  owned by a different workstream or by nobody — see docs/contracts.md §1

Only FAIL sets a non-zero exit. This job is advisory (non-blocking) in CI until M5 —
see .github/workflows/ci.yml and docs/verification.md.

Standard library only, and deliberately so: reading PNG/JPEG dimensions by hand is 30
lines and avoids making Pillow a contributor prerequisite for a theme that ships with
"no Node, no npm, no build toolchain" on the tin.

Python 3.8+.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

REQUIRED_THEME_TOML_FIELDS = [
    "name", "license", "licenselink", "description", "homepage",
    "tags", "features", "min_version",
]

SCREENSHOT_MIN = (1500, 1000)
THUMBNAIL_MIN = (900, 600)
ASPECT = 3 / 2
ASPECT_TOLERANCE = 0.01

# Substrings that indicate a live third-party tracking credential. specs/009 §2 forbids
# these anywhere in exampleSite; it is also why the showcase demo is exampleSite and not
# citizix.com, which carries AdSense, GTM and GA4.
TRACKING_PATTERNS = [
    (re.compile(r"\bUA-\d{4,}-\d+\b"), "Google Analytics (Universal) property ID"),
    (re.compile(r"\bG-[A-Z0-9]{8,}\b"), "GA4 measurement ID"),
    (re.compile(r"\bGTM-[A-Z0-9]{4,}\b"), "Google Tag Manager container ID"),
    (re.compile(r"\bca-pub-\d{10,}\b"), "AdSense publisher ID"),
    (re.compile(r"\bpub-\d{16}\b"), "AdSense publisher ID"),
    (re.compile(r"googletagmanager\.com"), "Google Tag Manager host"),
    (re.compile(r"google-analytics\.com"), "Google Analytics host"),
    (re.compile(r"\bFB-\d{6,}\b|facebook\.net/en_US/fbevents"), "Facebook pixel"),
    (re.compile(r"\bhotjar\b", re.IGNORECASE), "Hotjar"),
    (re.compile(r"\bplausible\.io\b"), "Plausible (host, may be legitimate but must be opt-in)"),
]

# Markdown links/images that are not absolute. specs/009 §2: the README is carried onto
# themes.gohugo.io, where a relative link resolves against the wrong origin and 404s.
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
MD_REF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HTML_SRC_RE = re.compile(r"""<(?:img|a)\b[^>]*?(?:src|href)\s*=\s*["']([^"']+)""", re.IGNORECASE)


class Findings:
    def __init__(self):
        self.items = []

    def add(self, level, message, detail=""):
        self.items.append((level, message, detail))

    fail = lambda self, m, d="": self.add("FAIL", m, d)   # noqa: E731
    todo = lambda self, m, d="": self.add("TODO", m, d)   # noqa: E731
    note = lambda self, m, d="": self.add("NOTE", m, d)   # noqa: E731
    ok = lambda self, m, d="": self.add("ok", m, d)       # noqa: E731


def load_toml(path: Path):
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        pass
    try:
        import tomli  # type: ignore
        return tomli.loads(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        return None


def toml_top_level_keys(text: str):
    """Crude fallback for Python < 3.11 with no tomli: top-level bare keys and tables."""
    keys = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            keys.add(line.strip("[]").split(".")[0])
        elif "=" in line:
            keys.add(line.split("=", 1)[0].strip())
    return keys


def image_size(path: Path):
    """(width, height) for PNG/JPEG, or None. No third-party imaging library."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        if data[12:16] != b"IHDR":
            return None
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack(">HH", data[i + 5:i + 9])
                return width, height
            i += 2 + length
    return None


def check_image(repo: Path, stem: str, minimum, f: Findings):
    matches = [p for p in (repo / "images").glob(f"{stem}.*")
               if p.suffix.lower() in (".png", ".jpg", ".jpeg")] if (repo / "images").is_dir() else []
    if not matches:
        f.todo(f"images/{stem}.{{png,jpg}} does not exist",
               f"required minimum {minimum[0]}x{minimum[1]}, 3:2. Not producible until the "
               f"theme renders (M5).")
        return
    for path in matches:
        size = image_size(path)
        rel = path.relative_to(repo).as_posix()
        if size is None:
            f.fail(f"{rel}: could not read image dimensions")
            continue
        w, h = size
        problems = []
        if w < minimum[0] or h < minimum[1]:
            problems.append(f"{w}x{h} is below the {minimum[0]}x{minimum[1]} minimum")
        if abs((w / h) - ASPECT) > ASPECT_TOLERANCE:
            problems.append(f"aspect ratio {w / h:.3f} is not 3:2 ({ASPECT:.3f})")
        if problems:
            f.fail(f"{rel}: " + "; ".join(problems))
        else:
            f.ok(f"{rel}: {w}x{h}, 3:2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--strict", action="store_true",
                        help="treat TODO as failure — for the M5 release gate")
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    f = Findings()

    # ── theme.toml ────────────────────────────────────────────────────────────────────
    theme_toml = repo / "theme.toml"
    for bad in ("theme.yaml", "theme.yml", "theme.json"):
        if (repo / bad).exists():
            f.fail(f"{bad} exists — the showcase accepts TOML only (specs/009 §2)")
    if not theme_toml.is_file():
        f.fail("theme.toml is missing")
    else:
        text = theme_toml.read_text(encoding="utf-8")
        data = load_toml(theme_toml)
        keys = set(data) if data is not None else toml_top_level_keys(text)
        missing = [k for k in REQUIRED_THEME_TOML_FIELDS if k not in keys]
        if missing:
            f.fail(f"theme.toml missing required field(s): {', '.join(missing)}")
        else:
            f.ok("theme.toml carries every required field")
        if "author" not in keys:
            f.fail("theme.toml has no [author] table")
        else:
            f.ok("theme.toml [author] present")
        if data is not None:
            min_version = str(data.get("min_version", ""))
            if min_version != "0.146.0":
                f.fail(f"theme.toml min_version is {min_version!r}, ADR-0 declares 0.146.0")
            else:
                f.ok("theme.toml min_version = 0.146.0 matches ADR-0")

    # ── root hugo.toml [module.hugoVersion] ───────────────────────────────────────────
    root_cfg = repo / "hugo.toml"
    if not root_cfg.is_file():
        f.fail("root hugo.toml is missing — the showcase now requires it (specs/009 §2)")
    else:
        data = load_toml(root_cfg)
        if data is not None:
            hv = data.get("module", {}).get("hugoVersion")
            if not isinstance(hv, dict):
                f.fail("root hugo.toml has no [module.hugoVersion] table")
            else:
                f.ok(f"root hugo.toml [module.hugoVersion] = {hv}")
                if str(hv.get("min", "")) != "0.146.0":
                    f.fail(f"[module.hugoVersion].min is {hv.get('min')!r}, ADR-0 declares 0.146.0")
        elif "[module.hugoVersion]" not in root_cfg.read_text(encoding="utf-8"):
            f.fail("root hugo.toml has no [module.hugoVersion] table")

    # ── LICENSE ───────────────────────────────────────────────────────────────────────
    lic = repo / "LICENSE"
    if not lic.is_file():
        f.fail("LICENSE is missing")
    elif "MIT" not in lic.read_text(encoding="utf-8"):
        f.fail("LICENSE does not look like MIT")
    else:
        f.ok("LICENSE present and MIT")

    # ── README absolute URLs ──────────────────────────────────────────────────────────
    readme = repo / "README.md"
    if not readme.is_file():
        f.fail("README.md is missing")
    else:
        text = readme.read_text(encoding="utf-8")
        relative = []
        for match in MD_LINK_RE.findall(text) + MD_REF_RE.findall(text) + HTML_SRC_RE.findall(text):
            target = match.strip("<>")
            if target.startswith("#"):
                continue    # in-page anchor, resolves correctly anywhere
            if not re.match(r"^(https?:)?//|^mailto:", target):
                relative.append(target)
        if relative:
            f.note(
                f"README.md has {len(relative)} relative link(s): "
                + ", ".join(sorted(set(relative))[:8]),
                "They break when the README is carried onto themes.gohugo.io (specs/009 §2). "
                "README.md is owned by NOBODY per docs/contracts.md §1 — fix in a separate PR.",
            )
        else:
            f.ok("README.md uses absolute URLs only")

    # ── exampleSite ───────────────────────────────────────────────────────────────────
    example = repo / "exampleSite"
    if not example.is_dir():
        f.fail("exampleSite/ is missing")
    else:
        cfg = example / "hugo.toml"
        if not cfg.is_file():
            f.fail("exampleSite/hugo.toml is missing")
        else:
            data = load_toml(cfg)
            base = (data or {}).get("baseURL", "")
            if data is not None and not base:
                f.fail("exampleSite/hugo.toml declares no baseURL")
            else:
                f.ok(f"exampleSite baseURL = {base or '(unparsed)'}")

        hits = []
        for path in sorted(example.rglob("*")):
            if not path.is_file() or path.suffix.lower() in (".png", ".jpg", ".woff2", ".ico"):
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for pattern, label in TRACKING_PATTERNS:
                if pattern.search(body):
                    hits.append(f"{path.relative_to(repo).as_posix()}: {label}")
        if hits:
            for hit in hits:
                f.fail(f"live tracking credential in exampleSite — {hit}")
        else:
            f.ok("no live tracking credentials in exampleSite")

    # ── Screenshots ───────────────────────────────────────────────────────────────────
    check_image(repo, "screenshot", SCREENSHOT_MIN, f)
    check_image(repo, "tn", THUMBNAIL_MIN, f)

    # ── Things that cannot be checked from the filesystem ─────────────────────────────
    f.note("public demo site building against latest Hugo",
           "specs/009 §3 — must be the deployed exampleSite, never citizix.com. "
           "Verified by the scheduled latest-Hugo job, not by this script.")
    f.note("submission is a PR to gohugoio/hugoThemesSiteBuilder",
           "add the URL to themes.txt in lexicographical order; the Netlify deploy "
           "preview is the gate. The old hugoThemes issue process and reviewTheme.sh "
           "are gone (specs/009 §1).")

    # ── Report ────────────────────────────────────────────────────────────────────────
    print("Hugo Themes showcase compliance — specs/009 §2")
    order = {"FAIL": 0, "TODO": 1, "NOTE": 2, "ok": 3}
    for level, message, detail in sorted(f.items, key=lambda i: order[i[0]]):
        print(f"  [{level:<4}] {message}")
        if detail:
            print(f"           {detail}")

    fails = [i for i in f.items if i[0] == "FAIL"]
    todos = [i for i in f.items if i[0] == "TODO"]
    print()
    print(f"  {len(fails)} fail, {len(todos)} todo, "
          f"{len([i for i in f.items if i[0] == 'NOTE'])} note, "
          f"{len([i for i in f.items if i[0] == 'ok'])} ok")

    if fails or (args.strict and todos):
        print("FAIL: showcase compliance")
        return 1
    print("PASS: showcase compliance (advisory — TODOs remain, see above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
