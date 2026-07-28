/* engine.js — tokenising and ranking for the metadata-only index.
   No DOM in this file. It is the half of the chunk that is worth reasoning about
   on its own, and keeping it DOM-free is what makes that possible.

   The index holds four short fields per document (title, terms, summary, date), so
   there is nothing here that resembles a full-text engine: no stemmer, no inverted
   index, no BM25. Over 490 documents of ~200 characters each, a linear scan with
   `indexOf` runs in well under a millisecond, and every byte spent on cleverness
   comes out of a 3,000 B gzipped budget that also has to pay for the UI. */

/* Whitespace-separated, lower-cased. Deliberately NOT a `\W` split: `c++`, `ci/cd`,
   `nginx.conf` and `k8s-node` are exactly the queries this corpus attracts, and
   splitting them into fragments makes every one of them match less well, not more. */
export function tokenise(q) {
  return q.toLowerCase().trim().split(/\s+/).filter(Boolean);
}

/* Lower-cased haystacks, computed once per document at load rather than per
   keystroke. `_t`/`_g`/`_s` are attached to the parsed object; the index itself is
   never mutated on disk. */
export function prepare(docs) {
  for (const d of docs) {
    d._t = (d.t || '').toLowerCase();
    d._g = (d.g || []).join(' ').toLowerCase();
    d._s = (d.s || '').toLowerCase();
  }
  return docs;
}

/* AND across terms, weighted sum within a term.
   A document that misses any term scores zero and is dropped — with a metadata-only
   index the fields are short enough that OR returns almost the whole archive for a
   two-word query, which is worse than no results.

   Weights: a title prefix beats a title word beats a title substring beats a tag
   beats the summary. The summary is worth 1 because it is the field most likely to
   contain an incidental match. */
export function rank(docs, terms, max) {
  const scored = [];
  for (const d of docs) {
    let total = 0;
    for (const t of terms) {
      let s = 0;
      const i = d._t.indexOf(t);
      if (i === 0) s += 10;
      else if (i > 0) s += d._t.charCodeAt(i - 1) === 32 ? 8 : 5;
      if (d._g.indexOf(t) !== -1) s += 4;
      if (d._s.indexOf(t) !== -1) s += 1;
      if (!s) { total = 0; break; }
      total += s;
    }
    if (total) scored.push([total, d]);
  }
  /* Newest wins a tie: the archive is technical and a 2024 answer usually beats the
     2021 one it supersedes. Dates are YYYY-MM-DD so a string compare is a date
     compare, and a document with no date sorts last. */
  scored.sort((a, b) => b[0] - a[0] || (b[1].d || '').localeCompare(a[1].d || ''));
  return { total: scored.length, hits: scored.slice(0, max).map((x) => x[1]) };
}
