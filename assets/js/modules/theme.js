/* theme.js — colour theme toggle.
   OWNED BY: the design-system workstream.

   Pairs with layouts/_partials/head/theme-guard.html, which has already stamped
   <html data-theme> before first paint. This module owns the *interactive* half.

   ADR-4 behaviour contracts, all of which the original proposal omitted:
     * every localStorage access wrapped in try/catch, with defined behaviour when
       storage is unavailable (the toggle still works, it just does not persist);
     * when the mode is "auto", respond to LIVE system theme changes;
     * the storage key is versioned — runbook:theme:v1;
     * CSS is already correct before this file executes.

   The toggle is rendered `hidden` in the markup and unhidden here, so a control that
   cannot work is never shown (specs/006 ADR-5). */

const KEY = 'runbook:theme:v1';
const MODES = ['auto', 'light', 'dark'];

function read() {
  try {
    const v = localStorage.getItem(KEY);
    return MODES.includes(v) ? v : null;
  } catch (e) {
    return null;
  }
}

function write(mode) {
  try {
    localStorage.setItem(KEY, mode);
  } catch (e) {
    /* Private mode, disabled storage, quota. The toggle still works for this page
       view; it simply does not persist. Never let this throw. */
  }
}

/* <meta name="theme-color"> — specs/003 §3.2.

   The value is READ BACK OUT OF THE CASCADE rather than written as a literal here.
   A hard-coded '#0d1117' in this file is a second copy of a token, and the copy is
   the one that goes stale the first time the palette moves; getComputedStyle always
   returns whatever tokens.css currently says, including the `auto` case, where the
   media query has already resolved it for us.

   theme-guard.html emits the no-JS version as a pair of media-scoped metas. That is
   correct for `auto` but cannot express "the reader chose dark on a light OS", so
   the first thing done here is to collapse the pair into one unconditional meta. */
function syncMeta(root) {
  const metas = document.head.querySelectorAll('meta[name="theme-color"]');
  if (!metas.length) return;
  for (let i = 1; i < metas.length; i++) metas[i].remove();
  const meta = metas[0];
  meta.removeAttribute('media');
  const bg = getComputedStyle(root).getPropertyValue('--rb-color-bg').trim();
  if (bg) meta.setAttribute('content', bg);
}

export function initTheme() {
  const root = document.documentElement;
  const button = document.querySelector('[data-rb-theme-toggle]');
  let mode = read() || root.dataset.theme || 'auto';

  const apply = (next) => {
    mode = next;
    root.dataset.theme = next;
    if (button) button.setAttribute('data-rb-theme-state', next);
    /* The custom property is read after the attribute is stamped, but the style
       recalculation it forces is what makes the value correct — so the order here
       is load-bearing, not incidental. */
    syncMeta(root);
  };

  apply(mode);

  /* Live system changes, for `auto`. Registered even when the toggle is switched
     off in config (params.runbook.showThemeToggle = false), because `auto` still
     has to track the OS in that case — the meta is the only thing that needs help,
     CSS repaints on its own. addListener is the pre-Safari-14 spelling and is kept
     because iOS Safari is in the support matrix (specs/007 §3.6). */
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const onSystemChange = () => { if (mode === 'auto') apply('auto'); };
  if (mq.addEventListener) mq.addEventListener('change', onSystemChange);
  else if (mq.addListener) mq.addListener(onSystemChange);

  if (!button) return;
  button.hidden = false;
  button.addEventListener('click', () => {
    apply(MODES[(MODES.indexOf(mode) + 1) % MODES.length]);
    write(mode);
  });
}
