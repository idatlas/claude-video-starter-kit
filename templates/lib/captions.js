/* Burned-in captions. The kit turns words.json into phrases (DATA.phrases); this draws them.
   project.json "captions":
     "mode": "phrase"  whole phrase at once (default, easiest to read)
             "karaoke" whole phrase, the word being spoken is highlighted
             "pop"     words appear one by one as they're spoken
             "off"
     "position": "bottom" | "top"
     "topDuring": [[12.0, 15.5], ...]  move captions to the top for these stretches (seconds),
                  e.g. while you click a button at the bottom of the screen
     "style": any CSS variable below, e.g. {"--cap-color": "#FFE14D", "--cap-size": "5.4vh"} */
(function () {
  const D = window.DATA || {};
  const C = { el: null, cur: -1 };
  C.mount = (parent) => {
    const cfg = D.captions || {};
    if (!D.phrases || cfg.mode === 'off') return;
    const el = document.createElement('div');
    el.className = `captions ${cfg.mode || 'phrase'} ${cfg.position || 'bottom'}`;
    K.vars(el, cfg.style);
    parent.appendChild(el);
    C.el = el;
  };
  C.update = (t) => {
    if (!C.el) return;
    const P = D.phrases;
    let k = -1;
    for (let i = 0; i < P.length; i++) if (t >= P[i].start - 0.05 && t < P[i].hold) { k = i; break; }
    if (k !== C.cur) {
      C.cur = k;
      C.el.innerHTML = k < 0 ? '' : '<span class="cap-line">' +
        P[k].words.map(w => `<span class="w">${K.esc(w.word)}</span>`).join(' ') + '</span>';
    }
    const top = ((D.captions || {}).topDuring || []).some(r => t >= r[0] && t < r[1]);
    C.el.classList.toggle('top', top || (D.captions || {}).position === 'top');
    if (k < 0) return;
    const ph = P[k], mode = (D.captions || {}).mode || 'phrase';
    C.el.style.opacity = Math.min(K.prog(t, ph.start - 0.05, ph.start + 0.07), 1 - K.prog(t, ph.hold - 0.08, ph.hold));
    C.el.querySelectorAll('.w').forEach((s, i) => {
      const w = ph.words[i];
      s.classList.toggle('now', t >= w.start && t < (ph.words[i + 1] ? ph.words[i + 1].start : ph.hold));
      if (mode === 'pop') {
        const p = K.prog(t, w.start - 0.02, w.start + 0.14);
        s.style.opacity = p > 0 ? 1 : 0;
        s.style.transform = `scale(${p > 0 ? K.lerp(0.75, 1, K.ease.back(p)) : 0.75})`;
      }
    });
  };
  window.Captions = C;
})();
