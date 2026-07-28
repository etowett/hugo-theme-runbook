/* code.js — copy button, wrap toggle, overflow detection.
   OWNED BY: the code-block workstream.

   This is the largest single consumer of the 3 KB core budget, and it runs against
   pages carrying a median of 16 code blocks and a maximum of 158. Per-block cost is a
   real number here, not a rounding error, so:

     * ONE delegated click listener on the document, not 158 button listeners;
     * ONE resize listener, rAF-coalesced, not a ResizeObserver per block;
     * every layout READ in measure() happens before any layout WRITE, so a resize
       costs one reflow rather than 158.

   Both controls are rendered `hidden` by the render hook and unhidden here — the copy
   button only when a clipboard path actually exists, the wrap toggle only on a block
   that actually overflows. With JavaScript off, or with the clipboard unavailable, the
   reader sees code and a language tag and no dead controls at all.

   ── REQ-CB-4 — what is copied ─────────────────────────────────────────────────
   The code element's textContent. NOT a data- attribute holding a second copy of the
   source: at 9,046 blocks that roughly doubles the code bytes in the HTML, and unlike
   the chrome markup around it, code does not repeat, so gzip cannot absorb it.

   NEVER heuristically strip "$ " or "# ". 1,389 lines across 318 posts (64% of the
   archive) begin with "$ ", mixed command-and-output blocks are routine, `#` may be a
   real shell comment and `$` may be data. Stripping is an explicit per-block opt-in
   via {prompt="$"} and is never inferred from content. */

const COPY = '[data-rb-copy]';
const WRAP = '[data-rb-wrap]';

let live = null;

/* One aria-live region per page, created on first use so that a page which never
   copies anything never grows a node for it. */
function announce(message) {
  if (!message) return;
  if (!live) {
    live = document.createElement('div');
    live.className = 'rb-code-live';
    live.setAttribute('role', 'status');
    live.setAttribute('aria-live', 'polite');
    document.body.appendChild(live);
  }
  /* Cleared first so that copying the same block twice announces twice — an
     unchanged textContent is not a change, and screen readers say nothing. */
  live.textContent = '';
  live.textContent = message;
}

/* Selection-based fallback for insecure contexts and browsers without the async
   clipboard. A detached textarea rather than a Range over the code element, because
   the text handed to the clipboard may be prompt-filtered and so is not what is on
   screen. */
function legacyCopy(text) {
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;inset-inline-start:-9999px;opacity:0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  } catch (e) {
    return false;
  }
}

function copyText(text, done) {
  const clip = navigator.clipboard;
  if (clip && clip.writeText) {
    clip.writeText(text).then(
      function () { done(true); },
      function () { done(legacyCopy(text)); }
    );
    return;
  }
  done(legacyCopy(text));
}

/* {prompt="$"} — keep only the lines that ARE commands, and drop the prompt from them.
   The prompt must be the first non-whitespace thing on the line, so `echo $HOME` is
   not mistaken for a prompt line. A command continued with a trailing backslash keeps
   its continuation lines verbatim; without that, copying a wrapped `kubeadm join`
   yields the first line only, which is worse than copying everything.

   If nothing matches, the author's prompt does not describe this block — fall back to
   copying it whole rather than putting an empty string on the clipboard. */
function stripPrompt(text, prompt) {
  const out = [];
  let cont = false;
  const lines = text.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (cont) {
      out.push(line);
      cont = /\\$/.test(line);
      continue;
    }
    const at = line.indexOf(prompt);
    if (at < 0 || line.slice(0, at).trim()) continue;
    let cmd = line.slice(at + prompt.length);
    if (cmd.charAt(0) === ' ') cmd = cmd.slice(1);
    out.push(cmd);
    cont = /\\$/.test(cmd);
  }
  return out.length ? out.join('\n') : text;
}

function codeText(item) {
  /* Normalise line endings; strip at most ONE structural newline left by the fence. */
  const text = item.code.textContent.replace(/\r\n?/g, '\n').replace(/\n$/, '');
  const prompt = item.block.getAttribute('data-rb-prompt');
  return prompt ? stripPrompt(text, prompt) : text;
}

export function initCode() {
  const blocks = document.querySelectorAll('.rb-code');
  if (!blocks.length) return;

  const items = [];
  const byBlock = new Map();
  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i];
    /* code[data-lang] is the CODE half of a line-numbered block; the gutter <code> in
       the other <td> carries no data-lang. That is what keeps line numbers out of the
       copy (REQ-CB-4) without any filtering. */
    const code = block.querySelector('code[data-lang]') || block.querySelector('code');
    if (!code) continue;
    const item = {
      block: block,
      code: code,
      /* The scroll container is the <pre> in every shape EXCEPT line numbers, where
         Chroma wraps a <table> in div.chroma and that wrapper is what scrolls — the
         <td> around the <pre> grows to its content and never constrains it. Measuring
         the wrong element here means tabindex on an element that does not scroll and
         no wrap toggle on a block that needs one. */
      pre: code.closest('div.chroma') || code.parentElement,
      wrap: block.querySelector(WRAP),
      over: false,
      wrapped: false
    };
    items.push(item);
    byBlock.set(block, item);
  }
  if (!items.length) return;

  /* REQ-CB-6 — tabindex ONLY where a block actually overflows. Chroma emits
     tabindex="0" on every <pre> and the render hook strips it, because overflow
     depends on viewport and font metrics and is not knowable at build time, and
     because Chrome 127+ already makes scroll containers focusable. At 18.2 blocks per
     post an unconditional tab stop per block is a real navigation tax.

     A wrapped block does not overflow, so it loses its tab stop — but it keeps its
     wrap button, or there would be no way to turn wrapping off again. */
  function measure() {
    const n = items.length;
    const over = [];
    for (let i = 0; i < n; i++) {
      const pre = items[i].pre;
      over.push(pre.scrollWidth - pre.clientWidth > 1);
    }
    for (let i = 0; i < n; i++) {
      const item = items[i];
      const isOver = over[i];
      if (item.wrap) {
        const hide = !(isOver || item.wrapped);
        if (item.wrap.hidden !== hide) item.wrap.hidden = hide;
      }
      if (isOver !== item.over) {
        item.over = isOver;
        if (isOver) item.pre.setAttribute('tabindex', '0');
        else item.pre.removeAttribute('tabindex');
      }
    }
  }

  let queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      measure();
    });
  }

  /* REQ-CB-3/4 — present the copy control only if there is a clipboard path to use.
     Otherwise the buttons stay `hidden` exactly as they were rendered. */
  let canCopy = !!(navigator.clipboard && navigator.clipboard.writeText);
  if (!canCopy) {
    try {
      canCopy = !!document.queryCommandSupported && document.queryCommandSupported('copy');
    } catch (e) {
      canCopy = false;
    }
  }
  if (canCopy) {
    const buttons = document.querySelectorAll(COPY);
    for (let i = 0; i < buttons.length; i++) buttons[i].hidden = false;
  }

  function flash(button, ok) {
    button.setAttribute('data-rb-state', ok ? 'ok' : 'err');
    announce(button.getAttribute(ok ? 'data-rb-copied' : 'data-rb-failed'));
    clearTimeout(button.rbTimer);
    button.rbTimer = setTimeout(function () {
      button.removeAttribute('data-rb-state');
      /* Both clipboard paths failed. Withdraw the control rather than leave a button
         that looks operable and is not. */
      if (!ok) button.hidden = true;
    }, 1600);
  }

  /* REQ-CB-5 — the wrap state is SESSION-LOCAL and deliberately not persisted.
     Wrapping is a property of the one long line being inspected, not a reading
     preference; persisting it silently re-breaks the next command the reader copies by
     eye. Nothing here touches storage, and what gets copied never changes with it. */
  function toggleWrap(item, button) {
    item.wrapped = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', item.wrapped ? 'true' : 'false');
    item.block.toggleAttribute('data-rb-wrapped', item.wrapped);
    measure();
  }

  /* ONE listener for every control on the page. */
  document.addEventListener('click', function (event) {
    const target = event.target;
    if (!target || !target.closest) return;
    const button = target.closest(COPY + ',' + WRAP);
    if (!button) return;
    const item = byBlock.get(button.closest('.rb-code'));
    if (!item) return;
    if (button.hasAttribute('data-rb-wrap')) {
      toggleWrap(item, button);
    } else {
      copyText(codeText(item), function (ok) { flash(button, ok); });
    }
  });

  window.addEventListener('resize', schedule, { passive: true });
  /* A late webfont changes the advance width of every glyph in the block, which
     changes what overflows. Cheap to wait for, wrong to ignore. */
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(schedule);

  measure();
}
