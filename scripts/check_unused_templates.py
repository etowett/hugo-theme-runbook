#!/usr/bin/env python3
"""Fail on templates the build never reached, except documented fallbacks.

WHY THIS IS NOT JUST `--panicOnWarning`
---------------------------------------
Hugo's --printUnusedTemplates emits a WARN per unreached template, so running it
under --panicOnWarning turns any unused template into a build failure. That is
mostly what we want: it caught four templates shipping with no fixture reaching
them (render-image, admonition, details, archive), each of which was a real gap.

It is wrong in one case. Runbook is published for general use, so it ships
fallbacks for inputs the demo site does not contain — list.html covers list kinds
that Hugo does not have today. Under a blanket rule the only way to go green is to
delete the fallback, which makes the theme worse for exactly the consumer it was
written for.

So: still fail by default, but allow entries that carry a written reason. Same
convention as .github/link-exclusions.json, and for the same reason — without a
recorded reason nobody can later tell a deliberate fallback from an oversight.

Usage:
    hugo … --printUnusedTemplates 2>&1 | tee build.log
    python3 scripts/check_unused_templates.py build.log .github/unused-templates-allowed.txt
"""

import re
import sys

UNUSED = re.compile(r"Template (\S+) is unused")


def load_allowed(path):
    allowed = {}
    malformed = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "::" not in line:
                malformed.append((lineno, line))
                continue
            tmpl, reason = line.split("::", 1)
            tmpl, reason = tmpl.strip(), reason.strip()
            if not reason:
                malformed.append((lineno, line))
                continue
            allowed[tmpl] = reason
    return allowed, malformed


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    log_path, allow_path = sys.argv[1], sys.argv[2]

    allowed, malformed = load_allowed(allow_path)
    if malformed:
        for lineno, line in malformed:
            print(f"FAIL: {allow_path}:{lineno} has no reason after '::' — {line}")
        print("\nEvery allowlist entry must carry a reason. See the header of that file.")
        return 1

    with open(log_path, encoding="utf-8", errors="replace") as fh:
        unused = sorted(set(UNUSED.findall(fh.read())))

    unexpected = [t for t in unused if t not in allowed]
    waived = [t for t in unused if t in allowed]

    for tmpl in waived:
        print(f"  allowed  {tmpl}\n           reason: {allowed[tmpl]}")

    # An allowlist entry that is no longer unused is stale: the template became
    # reachable, and leaving the waiver in place would hide it going dead again.
    stale = [t for t in allowed if t not in unused]
    for tmpl in stale:
        print(f"FAIL: {tmpl} is listed in {allow_path} but the build now reaches it.")
        print("      Delete the entry — a stale waiver silently covers a future regression.")

    for tmpl in unexpected:
        print(f"FAIL: {tmpl} is shipped but no fixture reaches it.")
        print("      Write a fixture that exercises it, or add it to")
        print(f"      {allow_path} with a reason.")

    if unexpected or stale:
        return 1

    print(f"PASS: unused templates — {len(unused)} unused, all documented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
