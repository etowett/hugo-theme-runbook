/* toc.js — table-of-contents scroll-spy.
   OWNED BY: the templates workstream. STUB — deliberately does nothing yet.

   ▸ SCROLL-SPY IS AN ENHANCEMENT, NOT A PREREQUISITE (specs/003 §3.4).

   The static anchor TOC ships first and must be fully usable without this file. This
   module adds active-state tracking ONLY IF its cost fits inside the 3 KB core budget
   alongside copy, wrap and overflow detection — that is open decision #3 in
   specs/006, and it is answered by measuring, not by assuming.

   If it does not fit, delete this module and its import. That is an acceptable
   outcome, not a failure.

   Implementation note: IntersectionObserver, not a scroll listener. And honour
   prefers-reduced-motion for any scroll or highlight animation. */

export function initToc() {
  /* Intentionally empty. */
}
