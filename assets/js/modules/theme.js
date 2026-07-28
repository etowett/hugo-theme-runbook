/* theme.js — colour theme toggle.
   OWNED BY: the design-system workstream. Working placeholder.

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

export function initTheme() {
  const button = document.querySelector('[data-rb-theme-toggle]');
  if (!button) return;

  const root = document.documentElement;
  let mode = read() || root.dataset.theme || 'auto';

  const apply = (next) => {
    mode = next;
    root.dataset.theme = next;
    button.setAttribute('data-rb-theme-state', next);
  };

  apply(mode);
  button.hidden = false;

  button.addEventListener('click', () => {
    apply(MODES[(MODES.indexOf(mode) + 1) % MODES.length]);
    write(mode);
  });

  // In "auto" the palette follows the OS; CSS handles the repaint, but anything
  // keyed off the resolved theme (meta theme-color, an icon) updates from here.
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const onSystemChange = () => { if (mode === 'auto') apply('auto'); };
  if (mq.addEventListener) mq.addEventListener('change', onSystemChange);
}
