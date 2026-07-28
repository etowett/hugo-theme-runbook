/* code.js — copy button, wrap toggle, overflow detection.
   OWNED BY: the code-block workstream. STUB — deliberately does nothing yet.

   This is the largest single consumer of the 3 KB core budget, and it runs against
   pages carrying a median of 16 code blocks and a maximum of 158. Per-block cost is a
   real number here, not a rounding error: prefer ONE delegated listener on the
   document over 158 listeners, and batch any layout reads.

   ── What this module must implement ───────────────────────────────────────────

   REQ-CB-3 — copy works on TOUCH and by KEYBOARD. The original "hover/focus-revealed
   button" has no trigger on a coarse pointer, and iOS Safari is in the browser matrix.
   The button is always present as a ghost control, at full contrast permanently under
   `@media (hover: none), (pointer: coarse)`, revealed by :focus-within for keyboard
   users, target >= 24x24 px.

   REQ-CB-4 — copy semantics:
     * copy the code element's textContent. Do NOT stash code in a data- attribute —
       at 9,046 blocks that roughly doubles code bytes in the HTML and blows the
       page-weight budget on its own;
     * normalise line endings to \n;
     * strip at most ONE structural trailing newline from the fence;
     * NEVER heuristically strip "$ " or "# ". `#` may be a real shell comment and `$`
       may be data. 1,389 lines across 318 posts (64% of the archive) begin with "$ ",
       and mixed command-and-output blocks are routine — which is precisely why
       stripping is an explicit per-block opt-in via {prompt="$"} and never inferred;
     * line-number gutters are excluded from the copy;
     * aria-live confirmation;
     * defined fallback when the Clipboard API is unavailable (insecure context, old
       browser): selection-based copy, and if that also fails, HIDE the button rather
       than presenting a broken one.

   REQ-CB-5 — per-block wrap toggle with aria-pressed, SESSION-LOCAL and NOT persisted.
   Wrapping is a property of the one long line being inspected, not a reading
   preference; persisting it silently re-breaks the next command the reader copies by
   eye. Copy behaviour is independent of visual wrapping.

   REQ-CB-6 — apply tabindex="0" ONLY to blocks that actually overflow, measured on
   load and on resize. Overflow cannot be determined from source (it depends on
   viewport and font metrics), and Chrome 127+ already makes scroll containers
   focusable — so unconditional tabindex adds a redundant tab stop per block, which at
   18 blocks per post is a real navigation tax. */

export function initCode() {
  /* Intentionally empty. */
}
