/* Shared helpers for every template. A template draws one frame when the kit calls
   window.render(t) with the time in seconds. Rule: what's on screen must depend only on t,
   never on the clock or Math.random, so frame 100 always looks the same. */
(function () {
  const D = window.DATA || {};
  const K = { D };
  K.clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  K.lerp = (a, b, t) => a + (b - a) * t;
  K.prog = (t, a, b) => (b <= a ? (t >= a ? 1 : 0) : K.clamp((t - a) / (b - a)));
  K.ease = {
    linear: t => t,
    out: t => 1 - Math.pow(1 - t, 3),
    in: t => t * t * t,
    inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    back: t => { const c = 1.70158, c3 = c + 1; return 1 + c3 * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); },
  };
  /* opacity for something shown from start to end, fading in and out */
  K.fade = (t, start, end, fin = 0.3, fout = 0.3) => {
    if (t < start || t >= end) return 0;
    return Math.min(fin ? K.prog(t, start, start + fin) : 1, fout ? 1 - K.prog(t, end - fout, end) : 1);
  };
  /* repeatable "random" number in 0..1 for a given seed */
  K.hash = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  K.asset = p => (/^(file|https?|data):/.test(p) ? p : new URL(p, D.base).href);
  K.loadImg = (img, src) => {
    if (img.dataset.src === src) return Promise.resolve();
    img.dataset.src = src; img.src = src;
    return img.decode().catch(() => {});
  };
  /* the image file for time t in an extracted video (frames are 00001.jpg ...) */
  K.seq = (info, t) => info.dir + String(K.clamp(Math.floor(t * (D.fps || 30) + 1e-6) + 1, 1, info.count)).padStart(5, '0') + '.jpg';
  K.vars = (el, vars) => { for (const k in vars || {}) el.style.setProperty(k.startsWith('--') ? k : '--' + k, vars[k]); };
  /* brand colors and fonts from project.json "brand" -> CSS variables */
  K.brand = () => {
    const b = D.brand || {}, r = document.documentElement.style;
    const map = { accent: '--accent', accent2: '--accent2', text: '--text', bg: '--bg', bg2: '--bg2', font: '--font', fontDisplay: '--font-display' };
    for (const k in map) if (b[k]) r.setProperty(map[k], /font/i.test(k) ? `'${b[k]}'` : b[k]);
  };
  K.esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  window.K = K;
})();
