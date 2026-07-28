#!/usr/bin/env python3
"""WCAG 2.2 AA gate for the Runbook palettes — specs/007 §3.1.

The check most themes lack. It parses the palette declarations out of the CSS,
resolves var() indirection, and asserts every foreground/background pair that a
reader can actually end up looking at, in BOTH themes, independently.

Three things it does that a plain token-vs-background sweep does not:

  1. Syntax tokens are checked against every background that can slide underneath
     them — the code background, the {hl_lines=...} band, and the diff line bands.
     A token that clears 4.5:1 on --rb-code-bg and fails on --rb-code-hl-bg is the
     normal outcome of tuning against one background, and nothing else catches it.
  2. Non-text pairs are checked at their own 3:1 threshold: focus rings, UI
     component boundaries, the highlighted-line marker. WCAG 1.4.11, not 1.4.3.
  3. Colour is checked as a SIGNAL, not just as contrast — deuteranopia and
     protanopia are simulated and the shell-critical tokens must stay perceptually
     apart afterwards, and no saturated syntax token may occupy the accent hue.

Standard library only, python3. Run from the repo root:

    python3 scripts/check_contrast.py [-v]
"""

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "assets" / "css"
AA_TEXT, AA_NONTEXT = 4.5, 3.0
DELTA_E_MIN = 12.0          # dichromatic separation floor, CIELAB dE76
LIGHTNESS_MIN = 1.50        # separation a pair may fall back on when hue collapses
ACCENT_HUE_GUARD = 25.0     # degrees a saturated syntax token must keep clear
HL_BAND_MIN = 1.35          # perceptibility floor for a background band; NOT WCAG

# ── parsing ─────────────────────────────────────────────────────────────────────

DECL = re.compile(r"(--rb-[\w-]+)\s*:\s*([^;]+);")


def blocks(text):
    """Yield (selector, body) for every top-level-ish rule, @media included."""
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", text, flags=re.S)):
        yield m.group(1).strip().replace("\n", " "), m.group(2)


def palettes(files):
    """Build {light: {...}, dark: {...}}. Dark inherits light, then overrides."""
    light, dark = {}, {}
    for f in files:
        text = (CSS / f).read_text()
        for sel, body in blocks(text):
            if "{" in sel:                       # the @media wrapper itself
                continue
            target = dark if 'data-theme="dark"' in sel or 'data-theme="auto"' in sel else (
                light if sel.strip().startswith(":root") and "data-theme" not in sel else None)
            if target is None:
                continue
            target.update(dict(DECL.findall(body)))
    merged = dict(light)
    merged.update(dark)
    return {"light": light, "dark": merged}


def resolve(name, pal, depth=0):
    """Follow var(--a, fallback) chains down to a literal colour."""
    v = pal.get(name, name).strip()
    if depth > 8:
        return None
    m = re.fullmatch(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+?)\s*)?\)", v)
    if m:
        got = resolve(m.group(1), pal, depth + 1)
        return got if got else (m.group(2) and rgb(m.group(2)))
    return rgb(v)


def rgb(v):
    v = v.strip()
    if not v.startswith("#"):
        return None
    h = v[1:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else None


# ── colour maths ────────────────────────────────────────────────────────────────

def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(c):
    r, g, b = (_lin(x) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def hsl(c):
    r, g, b = (x / 255 for x in c)
    mx, mn = max(r, g, b), min(r, g, b)
    d, l = mx - mn, (mx + mn) / 2
    if d == 0:
        return 0.0, 0.0, l
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    h = {r: (g - b) / d + (6 if g < b else 0), g: (b - r) / d + 2, b: (r - g) / d + 4}[mx]
    return h * 60, s, l


def lab(c):
    r, g, b = (_lin(x) for x in c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def simulate(c, kind):
    """Viénot/Brettel/Mollon dichromacy simulation on linear RGB."""
    r, g, b = (_lin(x) for x in c)
    L = 17.8824 * r + 43.5161 * g + 4.11935 * b
    M = 3.45565 * r + 27.1554 * g + 3.86714 * b
    S = 0.0299566 * r + 0.184309 * g + 1.46709 * b
    if kind == "protan":
        L = 2.02344 * M - 2.52581 * S
    else:                                              # deutan
        M = 0.494207 * L + 1.24827 * S
    lr = 0.080944 * L - 0.130504 * M + 0.116721 * S
    lg = -0.010249 * L + 0.054019 * M - 0.113615 * S
    lb = -0.000365 * L - 0.004122 * M + 0.693511 * S
    out = []
    for v in (lr, lg, lb):
        v = min(1.0, max(0.0, v))
        v = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        out.append(round(v * 255))
    return tuple(out)


def delta_e(a, b):
    return math.dist(lab(a), lab(b))


def hexof(c):
    return "#%02x%02x%02x" % c


# ── the assertions ──────────────────────────────────────────────────────────────

# Chroma token roles that are FOREGROUNDS. The two *-bg roles are backgrounds and
# are checked from the other side.
SYN_FG = ["comment", "punct", "literal", "builtin", "variable", "keyword", "name", "error"]

# Role pairs that were MEASURED to appear inside a single block, by running
# representative bash / yaml / json / python / go / dockerfile / sql / nginx / ini
# sources through Chroma and recording which classes came out together. Only these
# have to be tellable apart; `variable` (shell) and `name` (YAML/JSON keys), for
# instance, never share a block, and pretending they do costs real palette headroom.
#
# `punct` is deliberately absent. Operators and punctuation are STRUCTURE, not
# meaning — they are supposed to read as a near-text grey, and demanding that a
# reader distinguish `&&` from a command by colour would be inventing a requirement.
CO_OCCUR = [
    ("comment", "literal"), ("comment", "variable"), ("comment", "builtin"),
    ("comment", "keyword"), ("comment", "name"), ("literal", "variable"),
    ("literal", "builtin"), ("literal", "keyword"), ("literal", "name"),
    ("variable", "builtin"), ("variable", "keyword"), ("builtin", "keyword"),
    ("keyword", "name"),
]

# (foreground, background, threshold, what it is)
PAIRS = [
    ("--rb-color-text",        "--rb-color-bg",         AA_TEXT,    "body text on page"),
    ("--rb-color-text",        "--rb-color-bg-subtle",  AA_TEXT,    "body text on subtle surface"),
    ("--rb-color-text-muted",  "--rb-color-bg",         AA_TEXT,    "metadata on page"),
    ("--rb-color-text-muted",  "--rb-color-bg-subtle",  AA_TEXT,    "metadata on table header"),
    ("--rb-color-text-subtle", "--rb-color-bg",         AA_TEXT,    "subtle text on page"),
    ("--rb-color-text-subtle", "--rb-color-bg-subtle",  AA_TEXT,    "subtle text on subtle surface"),
    ("--rb-color-accent",      "--rb-color-bg",         AA_TEXT,    "link on page"),
    ("--rb-color-accent",      "--rb-color-bg-subtle",  AA_TEXT,    "link in blockquote/table"),
    ("--rb-color-accent-hover", "--rb-color-bg",        AA_TEXT,    "link:hover on page"),
    ("--rb-color-accent-contrast", "--rb-color-accent", AA_TEXT,    "skip-link text on accent"),
    ("--rb-color-focus",       "--rb-color-bg",         AA_NONTEXT, "focus ring on page"),
    ("--rb-color-focus",       "--rb-color-bg-subtle",  AA_NONTEXT, "focus ring on subtle surface"),
    ("--rb-color-focus",       "--rb-code-bg",          AA_NONTEXT, "focus ring inside a code block"),
    ("--rb-color-border-strong", "--rb-color-bg",       AA_NONTEXT, "control boundary (theme toggle)"),
    ("--rb-color-border-strong", "--rb-color-bg-subtle", AA_NONTEXT, "control boundary on subtle"),
    ("--rb-toc-fg",            "--rb-color-bg",         AA_TEXT,    "TOC entry"),
    ("--rb-toc-fg-active",     "--rb-color-bg",         AA_TEXT,    "TOC entry, selected"),
    ("--rb-toc-marker",        "--rb-color-bg",         AA_NONTEXT, "TOC active marker"),
    ("--rb-code-text",         "--rb-code-bg",          AA_TEXT,    "code, uncoloured"),
    ("--rb-code-text",         "--rb-code-output-bg",   AA_TEXT,    "code in an {output=true} block"),
    ("--rb-code-chrome-fg",    "--rb-code-bg",          AA_TEXT,    "copy/wrap control at rest"),
    ("--rb-code-chrome-fg",    "--rb-code-output-bg",   AA_TEXT,    "copy/wrap control on output block"),
    ("--rb-code-chrome-fg-hover", "--rb-code-bg",       AA_TEXT,    "copy/wrap control, hover"),
    ("--rb-code-gutter-fg",    "--rb-code-bg",          AA_TEXT,    "line numbers"),
    ("--rb-code-hl-border",    "--rb-code-bg",          AA_NONTEXT, "highlighted-line marker"),
]

# Backgrounds every syntax token has to survive landing on.
TOKEN_BACKGROUNDS = ["--rb-code-bg", "--rb-code-hl-bg", "--rb-syn-del-bg", "--rb-syn-ins-bg"]


def main():
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    pals = palettes(["tokens.css", "chroma-light.css", "chroma-dark.css"])
    failures, checks = [], 0

    for theme in ("light", "dark"):
        pal = pals[theme]
        print(f"\n{theme.upper()}")

        def check(fg, bg, need, label, kind="contrast"):
            nonlocal checks
            a, b = resolve(fg, pal), resolve(bg, pal)
            if a is None or b is None:
                failures.append(f"{theme}: unresolved colour in {label!r} ({fg} / {bg})")
                return
            checks += 1
            r = ratio(a, b)
            ok = r >= need
            if not ok:
                failures.append(f"{theme}: {label} — {r:.2f}:1, need {need}:1 ({fg} on {bg})")
            if verbose or not ok:
                print(f"  {'ok ' if ok else 'FAIL'} {r:6.2f}:1  (>={need})  {label}")

        for fg, bg, need, label in PAIRS:
            check(fg, bg, need, label)

        # Every syntax token, against every background that can sit under it.
        for role in SYN_FG:
            for bg in TOKEN_BACKGROUNDS:
                # A diff band only ever sits under the diff token itself.
                if bg.endswith("del-bg") and role != "keyword":
                    continue
                if bg.endswith("ins-bg") and role != "name":
                    continue
                check(f"--rb-syn-{role}", bg, AA_TEXT, f".{role} on {bg[5:]}")

        # The band has to be visible at all. WCAG's ratio is the wrong instrument for
        # two backgrounds — it is a luminance ratio, and near-black luminances are so
        # compressed that visibly distinct dark bands score ~1.1:1. So this is an
        # explicit perceptibility floor, documented as NOT a WCAG claim; the
        # conformant signal is --rb-code-hl-border above, checked at 3:1.
        for band in ("--rb-code-hl-bg", "--rb-syn-del-bg", "--rb-syn-ins-bg"):
            check(band, "--rb-code-bg", HL_BAND_MIN, f"{band[5:]} band is perceptible")

        # ── Colour as a SIGNAL, not just as contrast ────────────────────────────
        # specs/003 §3.2: "avoid red/green as the sole distinguishing signal". Made
        # testable: for every pair that shares a block, either the two survive
        # deuteranopia AND protanopia as distinct colours, or they are far enough
        # apart in lightness that hue is not carrying the distinction in the first
        # place. Failing both is the definition of "distinguished by hue alone",
        # and it is the failure a trichromatic reviewer cannot see.
        #
        # No palette of six hues can keep all six apart for a dichromat — the two
        # cone-response axes collapse to one. Pretending otherwise produces a gate
        # nobody can pass, so the escape hatch is lightness, which is exactly the
        # channel dichromats keep.
        pairs = [(f"--rb-syn-{a}", f"--rb-syn-{b}") for a, b in CO_OCCUR]
        pairs += [("--rb-code-text", f"--rb-syn-{r}") for r in SYN_FG if r != "punct"]
        for x, y in pairs:
            a, b = resolve(x, pal), resolve(y, pal)
            checks += 1
            ds = {k: delta_e(simulate(a, k), simulate(b, k)) for k in ("deutan", "protan")}
            light_sep = ratio(a, b)
            ok = light_sep >= LIGHTNESS_MIN or all(d >= DELTA_E_MIN for d in ds.values())
            how = "lightness" if light_sep >= LIGHTNESS_MIN else "hue"
            if not ok:
                failures.append(
                    f"{theme}: {x[5:]} vs {y[5:]} separated by hue alone and hue collapses — "
                    f"deutan dE {ds['deutan']:.1f}, protan dE {ds['protan']:.1f}, "
                    f"lightness {light_sep:.2f}:1")
            if verbose or not ok:
                print(f"  {'ok ' if ok else 'FAIL'} via {how:9} "
                      f"(dE d{ds['deutan']:.0f}/p{ds['protan']:.0f}, L {light_sep:.2f})  "
                      f"{x[5:]} vs {y[5:]}")

        # The accent hue is reserved for interaction (tokens.css).
        ah = hsl(resolve("--rb-color-accent", pal))[0]
        for role in SYN_FG:
            c = resolve(f"--rb-syn-{role}", pal)
            h, s, _ = hsl(c)
            checks += 1
            if s < 0.25:
                continue                                  # near-neutral, carries no hue
            dist = abs((h - ah + 180) % 360 - 180)
            ok = dist >= ACCENT_HUE_GUARD
            if not ok:
                failures.append(f"{theme}: .{role} sits {dist:.0f}° from the accent hue, need {ACCENT_HUE_GUARD}°")
            if verbose or not ok:
                print(f"  {'ok ' if ok else 'FAIL'} {dist:5.0f}deg from accent  .{role}")

    # <meta name="theme-color"> is a literal in a template, because a meta tag cannot
    # read a custom property. That makes it the one value in the design system that
    # can silently drift out of step with the palette, so it is asserted rather than
    # trusted. specs/003 §3.2.
    guard = (ROOT / "layouts" / "_partials" / "head" / "theme-guard.html").read_text()
    declared = re.findall(r'<meta name="theme-color" content="(#[0-9a-fA-F]{3,6})"', guard)
    for theme in ("light", "dark"):
        want = resolve("--rb-color-bg", pals[theme])
        checks += 1
        if not any(rgb(d) == want for d in declared):
            failures.append(
                f"{theme}: theme-guard.html declares theme-color {declared}, none of which is "
                f"--rb-color-bg {hexof(want)} — the meta has drifted from tokens.css")

    print(f"\n{checks} assertions over 2 themes")
    if failures:
        print(f"\n{len(failures)} FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("all pass — WCAG 2.2 AA, both themes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
