// test-playthrough.js — index.html'in TAMAMINI (fizik + girdi + olaylar + ekranlar)
// sahte DOM ile çalıştırıp baştan sona oynar. Çözücü yolunu birebir tuşlara döker.
const fs = require('fs');
const vm = require('vm');
const { C, solve, pathStr } = require('./solve.js');

const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const src = html.match(/<script>([\s\S]*?)<\/script>/)[1];

// --- minimal DOM/tarayıcı taklidi ---
let tNow = 0, rafCb = null;
const listeners = {};
function mkEl(id) {
  const cls = new Set(['overlay']);
  if (id === 'end') cls.add('hidden');
  return {
    id, style: {}, innerHTML: '', textContent: '', width: 960, height: 600,
    classList: { add: c => cls.add(c), remove: c => cls.delete(c), contains: c => cls.has(c) },
    addEventListener: (t, f) => { listeners[id + ':' + t] = f; },
    getContext: () => ctxProxy,
  };
}
const grad = { addColorStop() {} };
const ctxProxy = new Proxy({}, {
  get(t, p) {
    if (p === 'canvas') return els.cv;
    return (...a) => (String(p).startsWith('create') ? grad : undefined);
  },
  set() { return true; },
});
const els = { cv: mkEl('cv'), title: mkEl('title'), end: mkEl('end'), endStats: mkEl('endStats'), endRank: mkEl('endRank') };
const sandbox = {
  console, JSON, Math,
  document: { getElementById: id => els[id] },
  window: { innerWidth: 1280, innerHeight: 800, devicePixelRatio: 1 },
  addEventListener: (t, f) => { listeners['win:' + t] = f; },
  performance: { now: () => tNow },
  requestAnimationFrame: cb => { rafCb = cb; },
  localStorage: { _m: {}, getItem(k) { return this._m[k] ?? null; }, setItem(k, v) { this._m[k] = v; } },
};
vm.createContext(sandbox);
vm.runInContext(src + '\n;globalThis.__x = { G, LEVELS, isSettled, WAIT_TICKS, TILE };', sandbox);
const X = sandbox.__x;

let failures = 0;
function check(cond, msg) {
  console.log((cond ? '  ✓ ' : '  ✗ ') + msg);
  if (!cond) failures++;
}
// tam TICK adımlı kare pompalama (çözücüyle birebir aynı faz için)
function pumpTicks(n) {
  for (let i = 0; i < n; i++) {
    tNow += (1 / 120) * 1000;
    const cb = rafCb; rafCb = null;
    if (cb) cb(tNow);
  }
}
function pumpUntilSettled(cap) {
  let n = 0;
  while (X.G.mode === 'play' && X.G.s.status === 'play' && !X.isSettled(X.G.L, X.G.s) && n++ < cap) pumpTicks(1);
}
function pumpUntilMode(modes, cap) {
  let n = 0;
  while (!modes.includes(X.G.mode) && n++ < cap) pumpTicks(1);
}
function key(code) { listeners['win:keydown']({ code, preventDefault() {} }); }
const KEY = { left: 'ArrowLeft', right: 'ArrowRight', up: 'ArrowUp', down: 'ArrowDown' };

function playSolution(li) {
  const L = C.parseLevel(C.LEVELS[li]);
  const r = solve(L, C.makeState(L), true);
  console.log('BÖLÜM ' + (li + 1) + ' — çözüm: ' + pathStr(r.path));
  for (const a of r.path) {
    if (a === 'wait') pumpTicks(20);
    else { key(KEY[a]); pumpUntilSettled(4000); }
    if (X.G.s.status === 'dead') return { died: true, flips: r.flips };
    if (X.G.mode === 'winning') break;
  }
  return { died: false, flips: r.flips };
}

// --- senaryo ---
console.log('BAŞTAN SONA OYNANIŞ TESTİ');
pumpTicks(5);
check(X.G.mode === 'title', 'başlık ekranında bekliyor');
key('Enter');
check(X.G.mode === 'play' && X.G.li === 0, 'Enter ile oyun başladı (Bölüm 1)');

// BÖLÜM 1
pumpUntilSettled(4000); // başlangıç düşüşü (çözücü de aynısını yapar)
let r1 = playSolution(0);
check(!r1.died && X.G.mode === 'winning', 'Bölüm 1 çözümü ölümsüz tamamlandı');
pumpUntilMode(['play'], 400);
check(X.G.li === 1, 'Bölüm 2 yüklendi');

// BÖLÜM 2 — önce bilinçli saf hata, sonra temiz çözüm
pumpUntilSettled(4000);
key('ArrowRight'); // doğrudan dikenlere
pumpTicks(300);
check(X.G.deaths === 1, 'saf hamle dikende öldürdü (ölüm=1)');
check(X.G.mode === 'play' && X.G.s.status === 'play', 'hızlı yeniden doğuş çalıştı');
key('KeyR'); pumpTicks(2); // fazı sıfırla (çözücü tick=0 varsayar)
let r2 = playSolution(1);
check(!r2.died && X.G.mode === 'winning', 'Bölüm 2 çözümü (beklemeli) ölümsüz tamamlandı');
pumpUntilMode(['play'], 400);
check(X.G.li === 2, 'Bölüm 3 yüklendi');

// BÖLÜM 3 — önce R testi, sonra çözüm
pumpUntilSettled(4000);
key('ArrowLeft'); pumpUntilSettled(4000); // kutu kayar
check(X.G.levelFlips === 1, 'tek tuş hem oyuncuyu hem kutuyu kaydırdı');
key('KeyR'); pumpTicks(2);
check(X.G.levelFlips === 0 && X.G.mode === 'play', 'R odayı sıfırladı (kutu da başa döndü)');
let r3 = playSolution(2);
check(!r3.died, 'Bölüm 3 çözümü ölümsüz oynandı');
pumpUntilMode(['end'], 400);
check(X.G.mode === 'end', 'üç bölüm bitince final ekranı açıldı');
check(!els.end.classList.contains('hidden'), 'final katmanı görünür');
const expectedFlips = r1.flips + r2.flips + r3.flips + 2; // +1 saf hamle, +1 R-testi kaydırması
check(new RegExp('çevirme <b>' + expectedFlips + '<\\/b>').test(els.endStats.innerHTML),
  'finalde çevirme sayacı doğru (' + expectedFlips + ')');
check(/ölüm <b>1<\/b>/.test(els.endStats.innerHTML), 'finalde ölüm sayacı doğru (1)');
console.log('  final ekranı: ' + els.endStats.innerHTML.replace(/<br>/g, ' · ').replace(/<[^>]+>/g, ''));

key('KeyR');
check(X.G.mode === 'play' && X.G.li === 0, 'finalde R tüm oyunu baştan başlattı');

console.log(failures ? '\n' + failures + ' KONTROL BAŞARISIZ ✗' : '\nTÜM OYNANIŞ KONTROLLERİ GEÇTİ ✓');
process.exit(failures ? 1 : 0);
