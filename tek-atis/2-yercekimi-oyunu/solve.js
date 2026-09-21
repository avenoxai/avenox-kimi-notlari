// solve.js — index.html içindeki çekirdek fiziği birebir kullanarak
// her bölümün çözülebilir olduğunu Dijkstra ile kanıtlar.
// Kullanım: node solve.js            → tüm bölümleri doğrula
//           node solve.js --tune     → testere faz kayması öner
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const m = html.match(/\/\*==CORE-START==\*\/([\s\S]*?)\/\*==CORE-END==\*\//);
if (!m) { console.error('CORE bloğu bulunamadı'); process.exit(1); }
const C = new Function(m[1] + `
  return { LEVELS, parseLevel, makeState, cloneState, stateKey, stepOne,
           isSettled, settleInPlace, simulate, sawPos, DIRS, TILE, WAIT_TICKS };
`)();

const ARROW = { left: '←', right: '→', up: '↑', down: '↓', wait: '⏱' };

// (flips, ticks) sıralı ikili öbek
function makeHeap() {
  const h = [];
  const less = (a, b) => a.f < b.f || (a.f === b.f && a.t < b.t);
  return {
    size: () => h.length,
    push(it) {
      h.push(it);
      let i = h.length - 1;
      while (i > 0) { const p = (i - 1) >> 1; if (less(h[i], h[p])) { [h[i], h[p]] = [h[p], h[i]]; i = p; } else break; }
    },
    pop() {
      const top = h[0], last = h.pop();
      if (h.length) {
        h[0] = last;
        let i = 0;
        for (;;) {
          const l = 2*i + 1, r = l + 1; let s = i;
          if (l < h.length && less(h[l], h[s])) s = l;
          if (r < h.length && less(h[r], h[s])) s = r;
          if (s === i) break; [h[i], h[s]] = [h[s], h[i]]; i = s;
        }
      }
      return top;
    },
  };
}

// L: parseLevel çıktısı, s0: makeState çıktısı. allowWait: beklemeye izin var mı.
// En az çevirme (eşitse en kısa süre) çözümü arar.
function solve(L, s0, allowWait) {
  const actions = ['up', 'left', 'right', 'down'];
  if (allowWait && L.period > 1) actions.push('wait');
  const dist = new Map(), parent = new Map();
  const heap = makeHeap();
  const start = C.cloneState(s0);
  C.settleInPlace(L, start);
  if (start.status !== 'play') return { solvable: false, reason: 'başlangıç ölümcül: ' + start.status };
  const k0 = C.stateKey(L, start);
  dist.set(k0, { f: 0, t: 0 });
  heap.push({ k: k0, f: 0, t: 0, s: start });
  let best = null, explored = 0;
  while (heap.size()) {
    const cur = heap.pop();
    const dcur = dist.get(cur.k);
    if (!dcur || dcur.f !== cur.f || dcur.t !== cur.t) continue;
    if (best && (cur.f > best.f || (cur.f === best.f && cur.t >= best.t))) break;
    if (++explored > 3000000) throw new Error('durum patlaması (3M)');
    for (const a of actions) {
      const ns = C.cloneState(cur.s);
      const r = C.simulate(L, ns, a);
      if (r.res === 'dead' || r.res === 'noslide' || r.res === 'same' || r.res === 'timeout') continue;
      const nf = cur.f + (a === 'wait' ? 0 : 1);
      const nt = cur.t + r.ticks;
      if (r.res === 'win') {
        if (!best || nf < best.f || (nf === best.f && nt < best.t)) {
          best = { f: nf, t: nt, key: cur.k, last: a };
          parent.set('◆WIN', { prev: cur.k, a });
        }
        continue;
      }
      const k2 = C.stateKey(L, ns), od = dist.get(k2);
      if (!od || nf < od.f || (nf === od.f && nt < od.t)) {
        dist.set(k2, { f: nf, t: nt });
        parent.set(k2, { prev: cur.k, a });
        heap.push({ k: k2, f: nf, t: nt, s: ns });
      }
    }
  }
  if (!best) return { solvable: false, explored };
  // yolu geri kur
  const path = [];
  let node = parent.get('◆WIN'), key = node.prev;
  path.unshift(node.a);
  while (key !== k0) { const p = parent.get(key); path.unshift(p.a); key = p.prev; }
  return { solvable: true, flips: best.f, ticks: best.t, path, explored };
}

function pathStr(path) {
  // ardışık beklemeleri ⏱×n diye sıkıştır
  const out = [];
  for (const a of path) {
    if (a === 'wait' && out.length && out[out.length - 1].startsWith('⏱')) {
      const prev = out.pop();
      const n = prev.includes('×') ? +prev.split('×')[1] + 1 : 2;
      out.push('⏱×' + n);
    } else out.push(ARROW[a]);
  }
  return out.join(' ');
}

function verify() {
  let ok = true;
  for (let i = 0; i < C.LEVELS.length; i++) {
    const def = C.LEVELS[i];
    const L = C.parseLevel(def);
    const s0 = C.makeState(L);
    const t0 = Date.now();
    const r = solve(L, s0, true);
    const ms = Date.now() - t0;
    if (!r.solvable) {
      console.log(`BÖLÜM ${i + 1} (${def.name}): ÇÖZÜLEMEZ ✗  (${r.explored || 0} durum)`);
      ok = false;
      continue;
    }
    console.log(`BÖLÜM ${i + 1} (${def.name}): ÇÖZÜLEBİLİR ✓  par ${r.flips} çevirme · ${(r.ticks / 120).toFixed(2)} sn · ${r.explored} durum · ${ms} ms`);
    console.log('  çözüm: ' + pathStr(r.path));
    // beklemesiz de çözülebiliyor mu? (testere gerçekten zamanlama zorluyor mu)
    if (L.saws.length) {
      const r2 = solve(L, s0, false);
      if (r2.solvable && r2.flips <= r.flips) {
        console.log(`  UYARI: beklemesiz de ${r2.flips} çevirmeyle çözülüyor → testere zamanlama zorlamıyor: ${pathStr(r2.path)}`);
        ok = false;
      } else if (r2.solvable) {
        console.log(`  beklemesiz çözüm var ama +${r2.flips - r.flips} çevirme → testere işe yarıyor ✓`);
      } else {
        console.log('  beklemesiz çözüm yok → testere zamanlamayı zorunlu kılıyor ✓');
      }
    }
  }
  // bölüm 3: kutu olmadan çözülemez olmalı (kutu mekaniği zorunlu)
  {
    const def = C.LEVELS[2];
    const L = C.parseLevel(def);
    L.crateStarts = [];
    const r = solve(L, C.makeState(L), true);
    if (r.solvable) {
      console.log(`BÖLÜM 3 kutusuz da çözülüyor (${r.flips} çevirme): ${pathStr(r.path)} → kutu mekaniği atlanabiliyor ✗`);
      ok = false;
    } else {
      console.log('BÖLÜM 3: kutusuz çözüm yok → kutu + düğme mekaniği zorunlu ✓');
    }
  }
  console.log(ok ? '\nTÜM BÖLÜMLER DOĞRULANDI ✓' : '\nSORUN VAR ✗');
  process.exit(ok ? 0 : 1);
}

function tune() {
  // her testere için: beklemesiz çözülemez + beklemeli çözülebilir yapan ilk fazi bul
  for (let i = 0; i < C.LEVELS.length; i++) {
    const def = C.LEVELS[i];
    if (!def.saws.length) continue;
    const per = 2 * def.saws[0][4];
    let found = null;
    for (let off = 0; off < per; off += 20) {
      const d2 = JSON.parse(JSON.stringify(def));
      d2.saws[0][5] = off;
      const L = C.parseLevel(d2);
      const rW = solve(L, C.makeState(L), true);
      if (!rW.solvable) continue;
      const rN = solve(L, C.makeState(L), false);
      if (!rN.solvable || rN.flips > rW.flips) { found = { off, flips: rW.flips }; break; }
    }
    console.log(found
      ? `BÖLÜM ${i + 1}: önerilen faz kayması off=${found.off} (par ${found.flips})`
      : `BÖLÜM ${i + 1}: uygun faz bulunamadı, geometriyi gözden geçir`);
  }
}

if (require.main === module) {
  if (process.argv.includes('--tune')) tune();
  else verify();
}
module.exports = { C, solve, pathStr };
