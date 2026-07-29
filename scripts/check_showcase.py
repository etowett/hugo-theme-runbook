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

One requirement is about the world rather than about the tree, and is opt-in for that
reason. `--network` resolves the `demosite` URL over HTTP and FAILS on a non-2xx.
Without the flag the run is hermetic and touches nothing, so a pull request is never
gated on a host being reachable (specs/007 §3.5); `.github/workflows/scheduled.yml`
passes it daily at 22:00 UTC instead, two hours ahead of the showcase's own rebuild
(specs/009 §4). Presence alone was checked here until issue #46, which is how the field
sat for months at a URL that had never once resolved.

Standard library only, and deliberately so: reading PNG/JPEG dimensions by hand is 30
lines and avoids making Pillow a contributor prerequisite for a theme that ships with
"no Node, no npm, no build toolchain" on the tin. The same rule is why the demo site is
fetched with urllib rather than requests.

Python 3.8+.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import urllib.error
import urllib.request
from pathlib import Path

REQUIRED_THEME_TOML_FIELDS = [
    "name", "license", "licenselink", "description", "homepage",
    "tags", "features", "min_version",
]

SCREENSHOT_MIN = (1500, 1000)
THUMBNAIL_MIN = (900, 600)
ASPECT = 3 / 2
ASPECT_TOLERANCE = 0.01

# --network only. Long enough that a cold Netlify edge answers, short enough that a dead
# host does not hold a scheduled job open.
DEMO_TIMEOUT = 15.0
# Some hosts answer 403 to a checker with no User-Agent while working in a browser —
# .github/link-exclusions.json exists because of that class of false positive, and
# naming the checker is cheaper than an exclusion.
USER_AGENT = "runbook-check-showcase/1 (+https://github.com/etowett/hugo-theme-runbook)"

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


def demosite_value(data, text: str) -> str:
    """The declared demo URL, with the same parse fallback as the field check above.

    Anchored at the start of a line so the commented-out example in theme.toml — which
    is there to say what to restore, and when — is not read as a declaration.
    """
    if data is not None:
        return str(data.get("demosite") or "")
    match = re.search(r"""^\s*demosite\s*=\s*["']([^"']+)""", text, re.MULTILINE)
    return match.group(1) if match else ""


def fetch_status(url: str, timeout: float):
    """(status, detail) for a GET of `url`, following redirects.

    `status` is None when no response arrived at all — DNS failure, refused connection,
    TLS error, timeout. That case is kept distinct because it is the shape a demo site
    takes when it is deleted rather than merely broken, and because a traceback escaping
    a scheduled job tells whoever reads the tracking issue less than either.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)     # drain a little rather than the whole page
            return response.getcode(), response.geturl()
    except urllib.error.HTTPError as exc:       # a response, just not a usable one
        return exc.code, str(exc.reason or "")
    except urllib.error.URLError as exc:        # no response: DNS, refused, TLS
        return None, str(exc.reason)
    except OSError as exc:                      # socket.timeout on Python < 3.10
        return None, str(exc)


def check_demosite(data, text: str, f: Findings, network: bool, timeout: float) -> None:
    """specs/009 §2 — the public demo site, and the theme.toml field that points at it.

    The field is not in §2's required list (009-showcase-compliance.md:40); the demo
    itself is (:54). So an absent field is an honest report of undone work, while a URL
    that 404s fails the requirement and hides that it is failing — issue #46.
    """
    url = demosite_value(data, text)
    if not url:
        f.todo(
            "theme.toml declares no demosite — the demo is not deployed",
            "specs/009 §2 requires a public demo site that builds against latest Hugo "
            "(:54), and §3 requires it to be the deployed exampleSite, never "
            "citizix.com. netlify.toml builds it; the Netlify site still has to be "
            "created and connected. `demosite` itself is not one of §2's required "
            "theme.toml fields (:40), so its absence is honest — restore it, and delete "
            "the entry in .github/link-exclusions.json, the day the deploy is live.",
        )
        return

    if not re.match(r"^https?://", url):
        f.fail(f"theme.toml demosite is {url!r}, which is not an absolute http(s) URL")
        return

    if not network:
        f.note(f"demosite = {url} — declared, not resolved",
               "presence is not reachability, and presence was all this script checked "
               "until issue #46. Re-run with --network to fetch it; scheduled.yml does "
               "that daily so a demo going dark is found here rather than by the "
               "showcase's own rebuild (specs/009 §4).")
        return

    status, detail = fetch_status(url, timeout)
    if status is None:
        f.fail(f"demosite {url} could not be reached — {detail}",
               "no HTTP response at all — DNS failure, refused connection or timeout, "
               "which is the shape a demo takes when it is gone rather than merely "
               "broken. The showcase links a visitor straight at this URL "
               "(specs/009 §2).")
    elif 200 <= status < 300:
        landed = f" → {detail}" if detail and detail.rstrip("/") != url.rstrip("/") else ""
        f.ok(f"demosite {url} resolves — HTTP {status}{landed}")
    else:
        f.fail(f"demosite {url} returns HTTP {status} {detail}".rstrip(),
               "the showcase links a visitor straight at this URL, and its entry for "
               "the theme is only as good as what answers here (specs/009 §2).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--strict", action="store_true",
                        help="treat TODO as failure — for the M5 release gate")
    parser.add_argument("--network", action="store_true",
                        help="resolve the demosite URL over HTTP and fail on a non-2xx. "
                             "Off by default so a pull request never depends on a host "
                             "being up — scheduled.yml runs it daily instead")
    parser.add_argument("--timeout", type=float, default=DEMO_TIMEOUT,
                        help=f"seconds to wait for the demo site (default {DEMO_TIMEOUT:g})")
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
        check_demosite(data, text, f, args.network, args.timeout)

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
    #
    # The demo site used to be a NOTE here, deferring to "the scheduled latest-Hugo job".
    # That job builds exampleSite; it has never deployed it and it fetches nothing, so
    # the verification the note pointed at did not exist — issue #46. check_demosite()
    # above does it now, and --network is what makes it a check rather than a claim.
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
