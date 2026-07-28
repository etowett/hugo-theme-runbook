/* ═══════════════════════════════════════════════════════════════════════════════
   search/index.js — the /search/ page. A SEPARATE LAZY CHUNK.

   ▸ It is never imported from assets/js/runbook.js, which is frozen at three
     modules, and it is emitted by a second js.Build call from
     _partials/search/js.html so that it can only ever be requested by the one page
     that renders that partial. Every other page in the site is byte-identical with
     and without this feature.

       BUDGET: <= 3,000 B gzipped for this file AND engine.js together
       (specs/005 §3.1, ADR-5).

   ── SECURITY: THIS IS THE ONE GENUINE XSS SURFACE IN THE THEME ─────────────────

   Result titles, summaries and tags are author-controlled text that this file puts
   into the DOM. specs/008 M5 names search-result escaping in the security review,
   and the rule that satisfies it is structural rather than a habit:

       THERE IS NO `innerHTML`, NO `insertAdjacentHTML` AND NO `outerHTML` IN THIS
       FILE. Every string reaches the page as `textContent` or a text node.

   That includes the search-term highlighting, which is where a naive implementation
   reaches for `replace(re, '<mark>$1</mark>')` and hands the attacker the page:
   `mark()` below splits the string and builds real <mark> elements around real text
   nodes instead. `exampleSite/content/posts/search-result-escaping.md` carries a
   literal <script> tag in its title so the fixture goes through the index, the
   scorer, the highlighter and the DOM on every build.

   Link targets are checked too. `d.u` comes from Hugo's RelPermalink and cannot be
   hostile today, but assigning an unvalidated string to `.href` is how it stops
   being true later, so a target that is not a same-origin absolute path is dropped.

   ── DEGRADATION ────────────────────────────────────────────────────────────────

   The form is `display:none` in search.css until this file sets `data-rb-ready` on
   the root, so a reader without JavaScript is never shown an input that does
   nothing (success criterion 6, specs/001 §5). The HTML browse alternative beside
   it is server-rendered and always visible, so it survives this file failing to
   parse, failing to fetch, or never arriving at all.
   ═══════════════════════════════════════════════════════════════════════════════ */

import { tokenise, prepare, rank } from './engine.js';

const DEBOUNCE_MS = 120;

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

/* Append `text` to `parent`, wrapping every occurrence of every term in <mark>.
   Overlapping and repeated hits are collapsed by walking left to right and skipping
   any hit that starts before the cursor. Nothing here concatenates markup. */
function mark(parent, text, terms) {
  const low = text.toLowerCase();
  const hits = [];
  for (const t of terms) {
    let i = low.indexOf(t);
    while (i !== -1) {
      hits.push([i, i + t.length]);
      i = low.indexOf(t, i + t.length);
    }
  }
  hits.sort((a, b) => a[0] - b[0]);
  let pos = 0;
  for (const h of hits) {
    if (h[0] < pos) continue;
    if (h[0] > pos) parent.appendChild(document.createTextNode(text.slice(pos, h[0])));
    parent.appendChild(el('mark', null, text.slice(h[0], h[1])));
    pos = h[1];
  }
  parent.appendChild(document.createTextNode(text.slice(pos)));
}

export function initSearch() {
  const root = document.querySelector('[data-rb-search]');
  if (!root) return;

  const form = root.querySelector('[data-rb-search-form]');
  const input = root.querySelector('[data-rb-search-input]');
  const list = root.querySelector('[data-rb-search-results]');
  const status = root.querySelector('[data-rb-search-status]');
  if (!form || !input || !list || !status) return;

  const s = root.dataset;
  const max = parseInt(s.rbMax, 10) || 30;
  let docs = null;
  let loading = null;
  let timer = 0;

  /* Lazy in the second sense: the chunk only runs on /search/, and the index is only
     fetched once someone actually types. Landing on /search/ costs zero index bytes. */
  function load() {
    if (!loading) {
      loading = fetch(s.rbIndex, { credentials: 'same-origin' })
        .then((r) => {
          if (!r.ok) throw new Error(r.status);
          return r.json();
        })
        .then((j) => {
          if (!j || j.v !== 1 || !Array.isArray(j.docs)) throw new Error('schema');
          docs = prepare(j.docs);
        });
    }
    return loading;
  }

  function row(d, terms) {
    const li = el('li', 'rb-search-result');

    const h = el('h2', 'rb-search-result-title');
    /* Same-origin absolute path only. Rejects `javascript:` and `//host`. */
    if (typeof d.u === 'string' && /^\/(?!\/)/.test(d.u)) {
      const a = el('a');
      a.href = d.u;
      mark(a, d.t || d.u, terms);
      h.appendChild(a);
    } else {
      mark(h, d.t || '', terms);
    }
    li.appendChild(h);

    const bits = [];
    if (d.d) bits.push(d.d);
    if (d.g && d.g.length) bits.push(d.g.join(', '));
    if (bits.length) {
      const m = el('p', 'rb-search-result-meta');
      mark(m, bits.join(' · '), terms);
      li.appendChild(m);
    }

    if (d.s) {
      const p = el('p', 'rb-search-result-summary');
      mark(p, d.s, terms);
      li.appendChild(p);
    }
    return li;
  }

  function render(query) {
    const terms = tokenise(query);
    const r = rank(docs, terms, max);
    const frag = document.createDocumentFragment();
    for (const d of r.hits) frag.appendChild(row(d, terms));
    list.textContent = '';
    list.appendChild(frag);
    status.textContent = !r.total
      ? s.rbNone
      : r.total === 1
        ? s.rbOne
        : r.total > r.hits.length
          ? s.rbCapped.replace('{n}', r.total).replace('{m}', r.hits.length)
          : s.rbMany.replace('{n}', r.total);
  }

  function fail() {
    list.textContent = '';
    status.textContent = s.rbError;
  }

  function run() {
    const q = input.value.trim();
    /* Keep the URL shareable and the back button honest without adding history
       entries for every keystroke. This is also what makes the JSON-LD SearchAction
       target (`/search/?q={search_term_string}`) a real contract. */
    try {
      history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname);
    } catch (e) { /* file:// and sandboxed frames throw; search still works */ }
    if (!q) {
      list.textContent = '';
      status.textContent = '';
      return;
    }
    load().then(() => render(q), fail);
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearTimeout(timer);
    run();
  });
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(run, DEBOUNCE_MS);
  });

  /* Only now is the input real. Until this attribute exists search.css keeps the
     form out of the document's rendering entirely. */
  root.setAttribute('data-rb-ready', '');

  const initial = new URLSearchParams(location.search).get('q');
  if (initial) {
    input.value = initial;
    run();
  }
  input.focus({ preventScroll: true });
}

function boot() {
  try {
    initSearch();
  } catch (e) {
    /* Leaving the root without `data-rb-ready` is the correct failure: the form
       stays hidden and the server-rendered browse list is what the reader gets. */
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
