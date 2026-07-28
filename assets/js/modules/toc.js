/* toc.js — table-of-contents scroll-spy.
   OWNED BY: the templates workstream.

   ▸ SCROLL-SPY IS AN ENHANCEMENT, NOT A PREREQUISITE (specs/003 §3.4).

   The TOC that _partials/article/toc.html renders is a plain list of same-document
   links. It works with this file deleted, with JavaScript disabled, and in a text
   browser. All this module adds is `aria-current="true"` on the entry matching the
   heading you are currently reading — which the stylesheet turns into the active
   state, and which a screen reader announces as "current".

   OPEN DECISION #3 (specs/006) asked whether this fits the 3 KB gzipped core budget
   alongside copy, wrap and overflow detection. Answer: yes, comfortably — the
   measured cost is in the PR description, and the module is ~350 B gzipped of the
   budget. Had it not fitted, deleting this file and its import in runbook.js was the
   documented and acceptable outcome; that is still the correct move if the budget is
   ever contested, because nothing else depends on it.

   Design notes:

   * IntersectionObserver, never a scroll listener. A scroll handler runs on every
     frame of every scroll on a page whose p90 is 30 code blocks; the observer fires
     only when a heading actually crosses the trigger line.
   * The observer is only a *trigger*. The active heading is then chosen by a single
     pass over cached elements, because "the last heading above the fold" is not
     something intersection state alone can answer — with 10.8 headings per post,
     several are off-screen above at once and none of them is intersecting.
   * No animation, so there is nothing for prefers-reduced-motion to suppress. The
     module never scrolls anything: moving the viewport in response to reading
     position is exactly the behaviour that setting exists to prevent.
   * Everything is guarded. runbook.js isolates module failures, but a throw here
     would still be a console error on a reader's page. */

const TRIGGER_OFFSET = 96; /* px below the viewport top; clears a sticky header */

export function initToc() {
  const nav = document.querySelector('[data-rb-toc]');
  if (!nav || typeof IntersectionObserver === 'undefined') return;

  /* Map heading element → its TOC link, in document order. */
  const headings = [];
  const links = new Map();
  for (const link of nav.querySelectorAll('a[href^="#"]')) {
    const raw = link.getAttribute('href').slice(1);
    if (!raw) continue;
    let id = raw;
    try {
      id = decodeURIComponent(raw);
    } catch (e) {
      /* A malformed escape is not a reason to lose the whole TOC. */
    }
    const target = document.getElementById(id) || document.getElementById(raw);
    if (target && !links.has(target)) {
      links.set(target, link);
      headings.push(target);
    }
  }
  if (!headings.length) return;

  let active = null;

  function setActive(link) {
    if (link === active) return;
    if (active) active.removeAttribute('aria-current');
    active = link || null;
    if (active) active.setAttribute('aria-current', 'true');
  }

  function update() {
    let current = null;
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= TRIGGER_OFFSET) current = heading;
      else break;
    }
    /* Above the first heading, highlight nothing rather than lying about position. */
    setActive(current ? links.get(current) : null);
  }

  const observer = new IntersectionObserver(update, {
    rootMargin: `-${TRIGGER_OFFSET}px 0px 0px 0px`,
  });
  for (const heading of headings) observer.observe(heading);

  update();
}
