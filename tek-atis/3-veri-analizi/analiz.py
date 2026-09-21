# -*- coding: utf-8 -*-
"""Kuzey Rüzgarı - 6 aylık zarar analizi. rapor.html üretir (tamamen gömülü, çevrimdışı)."""
import pandas as pd, numpy as np, html, json

V = 'veri/'
sip = pd.read_csv(V+'siparisler.csv', parse_dates=['tarih'])
iad = pd.read_csv(V+'iadeler.csv', parse_dates=['iade_tarihi'])
rek = pd.read_csv(V+'reklam_harcamalari.csv', parse_dates=['tarih'])
uru = pd.read_csv(V+'urunler.csv')
sab = pd.read_csv(V+'sabit_giderler.csv')
sip['ay'] = sip.tarih.dt.to_period('M')
rek['ay'] = rek.tarih.dt.to_period('M')
AYLAR = ['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
AY_AD = ['Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos']

m = sip.merge(uru[['urun_id','birim_maliyet','kategori','urun_adi']], on='urun_id')
m['gross'] = m.adet*m.liste_fiyati
m['cogs']  = m.adet*m.birim_maliyet

# ---------- Aylık P&L (sipariş ayı bazında) ----------
ord_lvl = sip.groupby(['siparis_id','ay','tarih']).agg(
    sepet=('odenen_tutar','sum'), alinan=('musteriden_alinan_kargo','first'),
    maliyet=('kargo_maliyeti','first')).reset_index()
iadm = iad.merge(uru[['urun_id','birim_maliyet','kategori']], on='urun_id')\
          .merge(sip[['siparis_id','ay']].drop_duplicates(), on='siparis_id', how='left')
iadm['geri'] = np.where(iadm.yeniden_satilabilir=='evet', iadm.adet*iadm.birim_maliyet, 0)

pl = m.groupby('ay').agg(ciro=('odenen_tutar','sum'), gross=('gross','sum'),
                         indirim=('indirim_tutari','sum'), cogs=('cogs','sum'))
pl = pl.join([ord_lvl.groupby('ay').agg(alinan=('alinan','sum'), kargo=('maliyet','sum')),
              iadm.groupby('ay').agg(iade=('iade_edilen_tutar','sum'),
                                     iade_kargo=('iade_kargo_maliyeti','sum'),
                                     geri_maliyet=('geri','sum')),
              rek.groupby('ay').harcama.sum().rename('reklam'),
              sab.assign(ay=pd.to_datetime(sab.ay).dt.to_period('M')).groupby('ay').tutar.sum().rename('sabit')])
pl = pl.fillna(0)
pl['net_ciro'] = pl.ciro - pl.iade
pl['net_cogs'] = pl.cogs - pl.geri_maliyet
pl['katki'] = pl.net_ciro + pl.alinan - pl.net_cogs - pl.kargo - pl.iade_kargo
pl['kar'] = pl.katki - pl.reklam - pl.sabit
TOPLAM_ZARAR = pl.kar.sum()

# ---------- Neden 1: TikTok ----------
def kanal_net(k):
    ko = ord_lvl[ord_lvl.siparis_id.isin(sip.loc[sip.kanal==k,'siparis_id'].unique())]
    kl = m[m.kanal==k]
    ki = iadm[iadm.siparis_id.isin(ko.siparis_id)]
    katki = kl.odenen_tutar.sum() - ki.iade_edilen_tutar.sum() \
            - (kl.cogs.sum()-ki.geri.sum()) - ko.maliyet.sum() - ki.iade_kargo_maliyeti.sum()
    harc = rek[rek.kanal==k].harcama.sum()
    return katki, harc, katki-harc, kl.odenen_tutar.sum()

tt_katki, tt_harc, tt_net, tt_ciro = kanal_net('tiktok')
g_katki, g_harc, g_net, _ = kanal_net('google')
i_katki, i_harc, i_net, _ = kanal_net('instagram')
tt_roas = tt_ciro/tt_harc
tt_basabas = tt_harc/tt_katki
# aylık tiktok net (run-rate)
tt_ay = {}
for ay in AYLAR[2:]:
    ko = ord_lvl[(ord_lvl.ay.astype(str)==ay) & ord_lvl.siparis_id.isin(sip.loc[sip.kanal=='tiktok','siparis_id'].unique())]
    kl = m[(m.kanal=='tiktok') & (m.ay.astype(str)==ay)]
    ki = iadm[iadm.siparis_id.isin(ko.siparis_id)]
    k = kl.odenen_tutar.sum()-ki.iade_edilen_tutar.sum()-(kl.cogs.sum()-ki.geri.sum())-ko.maliyet.sum()-ki.iade_kargo_maliyeti.sum()
    h = rek[(rek.kanal=='tiktok') & (rek.ay.astype(str)==ay)].harcama.sum()
    tt_ay[ay] = (k, h, k-h)

# ---------- Neden 2: HOSGELDIN30 istismarı ----------
ilk = sip.groupby('musteri_id').tarih.min().rename('ilk_tarih')
s2 = sip.merge(ilk, on='musteri_id')
hg = s2[s2.kupon_kodu=='HOSGELDIN30']
hg_ord = hg.groupby(['siparis_id','ay']).agg(ind=('indirim_tutari','sum'),
        yeni=('tarih', lambda s: False)).reset_index()  # placeholder
hg2 = hg.assign(yeni=hg.tarih<=hg.ilk_tarih).groupby(['siparis_id','ay','yeni']).indirim_tutari.sum().reset_index()
abuse_ay = hg2[~hg2.yeni].groupby('ay').indirim_tutari.sum().reindex(pd.PeriodIndex(AYLAR, freq='M')).fillna(0)
legit_ay = hg2[hg2.yeni].groupby('ay').indirim_tutari.sum().reindex(pd.PeriodIndex(AYLAR, freq='M')).fillna(0)
ABUSE_TOP = abuse_ay.sum()
# maliyetin altında satış (Termos 1L + %30)
m['altinda'] = m.odenen_tutar < m.cogs
sub = m[m.altinda]
ALTI_ZARAR = (sub.cogs - sub.odenen_tutar).sum()

# ---------- Neden 3: Ayakkabı iadeleri ----------
ay_sold = m[m.kategori=='Ayakkabı']
ay_ret = iadm[iadm.kategori=='Ayakkabı']
diger_sold = m[m.kategori!='Ayakkabı'].adet.sum()
diger_ret = iadm[iadm.kategori!='Ayakkabı'].adet.sum()
REF_ORAN = diger_ret/diger_sold
AY_ORAN = ay_ret.adet.sum()/ay_sold.adet.sum()
excess = ay_ret.adet.sum() - REF_ORAN*ay_sold.adet.sum()
birim_marj = ay_sold.odenen_tutar.sum()/ay_sold.adet.sum() - ay_sold.cogs.sum()/ay_sold.adet.sum()
birim_maliyet = ay_sold.cogs.sum()/ay_sold.adet.sum()
ns = (ay_ret.yeniden_satilabilir=='hayır').mean()
rk = ay_ret.iade_kargo_maliyeti.sum()/ay_ret.adet.sum()
AYAKKABI_ETKI = excess*(birim_marj + rk + ns*birim_maliyet)

# ---------- Neden 4: Bedava kargo ----------
pre = ord_lvl[ord_lvl.tarih < '2026-05-15']
post = ord_lvl[ord_lvl.tarih >= '2026-05-15']
kucuk_post = post[post.sepet < 750]
KARGO_ETKI = len(kucuk_post)*139.0
kucuk_ay = kucuk_post.groupby('ay').size()
pre_pay = (pre.sepet<750).mean(); post_pay = (post.sepet<750).mean()

# ---------- Neden 5: Miks kayması ----------
mart_rate = m[m.ay.astype(str)=='2026-03'].groupby('kategori').apply(
    lambda g: g.cogs.sum()/g.gross.sum(), include_groups=False)
cat_gross = m.pivot_table(index='ay', columns='kategori', values='gross', aggfunc='sum')
mix_ratio = (cat_gross*mart_rate).sum(axis=1)/cat_gross.sum(axis=1)
base_ratio = mix_ratio.iloc[0]
MIKS_ETKI = (cat_gross.sum(axis=1)*(mix_ratio-base_ratio)).sum()
termos_pay = cat_gross['Termos ve Matara']/cat_gross.sum(axis=1)

# ---------- Masumlar ----------
hasar = iad[iad.neden=='hasarlı geldi'].iade_edilen_tutar.sum()
diger_kupon = sip[sip.kupon_kodu.isin(['BAHAR15','KAMP10'])].indirim_tutari.sum()

# ================= SVG grafik yardımcıları =================
C = dict(ink='#1a2233', mut='#5b6472', grid='#e6e8ee', pos='#1e9e6a', neg='#d64550',
         a1='#2563eb', a2='#f59e0b', a3='#8b5cf6', a4='#14b8a6', a5='#f97316', a6='#64748b')
def fmt(x, dec=0):
    s = f"{x:,.{dec}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return s
def mfmt(x):
    return f"{x/1e6:.1f}M".replace('.', ',')
def kfmt(x):
    if abs(x) >= 1e6: return mfmt(x)
    return f"{x/1e3:.0f}K"

def _axes(w, h, pl_, pr, pt, pb):
    return w-pl_-pr, h-pt-pb

def grouped_bars(series, labels, colors, w=720, h=300, ymin=None, ymax=None, fmtv=kfmt, legend=None, line=None, line_color=None, line_label=''):
    """series: list of lists (aynı uzunluk). line: ek çizgi serisi (sağ eksen yok, aynı ölçek)."""
    pl_, pr, pt, pb = 64, 16, 30, 44
    cw, ch = _axes(w, h, pl_, pr, pt, pb)
    allv = [v for s in series for v in s] + ([v for v in line if v is not None] if line else [])
    lo = min(0, min(allv)) if ymin is None else ymin
    hi = max(allv) if ymax is None else ymax
    if lo == hi: hi = lo+1
    rng = hi-lo; hi += rng*0.12; lo -= rng*0.05 if lo<0 else 0
    rng = hi-lo
    def Y(v): return pt + ch - (v-lo)/rng*ch
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for i in range(5):
        v = lo + rng*i/4; y = Y(v)
        out.append(f'<line x1="{pl_}" y1="{y:.1f}" x2="{w-pr}" y2="{y:.1f}" stroke="{C["grid"]}"/>')
        out.append(f'<text x="{pl_-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{fmtv(v)}</text>')
    n, k = len(labels), len(series)
    slot = cw/n; bw = min(46, slot*0.7/k)
    for gi, s in enumerate(series):
        for i, v in enumerate(s):
            x = pl_ + slot*i + slot/2 - (k*bw)/2 + gi*bw
            y0, y1 = Y(max(0,v)), Y(min(0,v))
            out.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw-3:.1f}" height="{max(1.5,y1-y0):.1f}" rx="3" fill="{colors[gi]}"/>')
    if line:
        pts = [(pl_+slot*i+slot/2, Y(v)) for i, v in enumerate(line) if v is not None]
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{line_color}" stroke-width="2.5"/>')
        for x, y in pts: out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{line_color}"/>')
    for i, lb in enumerate(labels):
        out.append(f'<text x="{pl_+slot*i+slot/2:.1f}" y="{h-pb+18}" text-anchor="middle" class="ax">{lb}</text>')
    out.append(f'<line x1="{pl_}" y1="{Y(0):.1f}" x2="{w-pr}" y2="{Y(0):.1f}" stroke="{C["ink"]}" stroke-width="1"/>')
    if legend:
        lx = pl_
        for j, name in enumerate(legend):
            out.append(f'<rect x="{lx}" y="8" width="10" height="10" rx="2" fill="{colors[j] if j<len(colors) else line_color}"/>')
            out.append(f'<text x="{lx+14}" y="17" class="lg">{html.escape(name)}</text>')
            lx += 14 + 7*len(name) + 26
    out.append('</svg>')
    return ''.join(out)

def stacked_bars(stacks, labels, colors, legend, w=720, h=300, fmtv=kfmt):
    pl_, pr, pt, pb = 64, 16, 30, 44
    cw, ch = _axes(w, h, pl_, pr, pt, pb)
    totals = [sum(s[i] for s in stacks) for i in range(len(labels))]
    hi = max(totals)*1.12
    def Y(v): return pt + ch - v/hi*ch
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for i in range(5):
        v = hi*i/4; y = Y(v)
        out.append(f'<line x1="{pl_}" y1="{y:.1f}" x2="{w-pr}" y2="{y:.1f}" stroke="{C["grid"]}"/>')
        out.append(f'<text x="{pl_-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{fmtv(v)}</text>')
    n = len(labels); slot = cw/n; bw = min(52, slot*0.55)
    for i in range(n):
        x = pl_ + slot*i + slot/2 - bw/2; acc = 0
        for gi, s in enumerate(stacks):
            v = s[i]
            y0, y1 = Y(acc+v), Y(acc)
            out.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(0.5,y1-y0):.1f}" fill="{colors[gi]}"/>')
            acc += v
        out.append(f'<text x="{pl_+slot*i+slot/2:.1f}" y="{h-pb+18}" text-anchor="middle" class="ax">{labels[i]}</text>')
    lx = pl_
    for j, name in enumerate(legend):
        out.append(f'<rect x="{lx}" y="8" width="10" height="10" rx="2" fill="{colors[j]}"/>')
        out.append(f'<text x="{lx+14}" y="17" class="lg">{html.escape(name)}</text>')
        lx += 14 + 7*len(name) + 26
    out.append('</svg>')
    return ''.join(out)

def barh(items, w=720, h=None, fmtv=lambda v: f"%{v:.1f}"):
    rh = 34; h = 20 + rh*len(items)
    mx = max(v for _, v in items)*1.15
    pl_ = 150
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for i, (name, v) in enumerate(items):
        y = 14 + rh*i
        bw = (w-pl_-70)*v/mx
        col = C['neg'] if v == max(x for _, x in items) else C['a6']
        out.append(f'<text x="{pl_-10}" y="{y+15}" text-anchor="end" class="ax2">{html.escape(name)}</text>')
        out.append(f'<rect x="{pl_}" y="{y}" width="{bw:.1f}" height="22" rx="4" fill="{col}"/>')
        out.append(f'<text x="{pl_+bw+8:.1f}" y="{y+15}" class="axv">{fmtv(v)}</text>')
    out.append('</svg>')
    return ''.join(out)

# ================= Grafikler =================
g1 = grouped_bars(
    [list(pl.ciro/1e6), list(pl.kar/1e6)], AY_AD,
    [C['a1'], C['pos']], legend=['Ciro (odenen)', 'Faaliyet kârı'], fmtv=lambda v: f"{v:.1f}M".replace('.',','))
# kâr barlarını renklendir: pozitif yeşil, negatif kırmızı (ayrı seriler)
g1 = grouped_bars(
    [list(pl.ciro/1e6), [max(0, k) for k in pl.kar/1e6], [min(0, k) for k in pl.kar/1e6]],
    AY_AD, [C['a1'], C['pos'], C['neg']], legend=['Ciro (ödenen)', 'Kâr', 'Zarar'],
    fmtv=lambda v: f"{v:.1f}M".replace('.',','))

sp = rek.pivot_table(index='ay', columns='kanal', values='harcama', aggfunc='sum').fillna(0)/1e6
g2 = stacked_bars([list(sp.get('google', [0]*6)), list(sp.get('instagram', [0]*6)),
                   list(sp.get('tiktok', [0]*6)), list(sp.get('eposta', [0]*6))],
                  AY_AD, [C['a1'], C['a3'], C['neg'], C['a4']],
                  ['Google', 'Instagram', 'TikTok', 'E-posta'], fmtv=lambda v: f"{v:.1f}M".replace('.',','))

roas_g = (m[m.kanal=='google'].groupby('ay').odenen_tutar.sum()/ (rek[rek.kanal=='google'].groupby('ay').harcama.sum()))
roas_i = (m[m.kanal=='instagram'].groupby('ay').odenen_tutar.sum()/ (rek[rek.kanal=='instagram'].groupby('ay').harcama.sum()))
roas_t = (m[m.kanal=='tiktok'].groupby('ay').odenen_tutar.sum()/ (rek[rek.kanal=='tiktok'].groupby('ay').harcama.sum())).reindex(pd.PeriodIndex(AYLAR, freq='M'))
g2b = grouped_bars([list(roas_g.values), list(roas_i.values)], AY_AD, [C['a1'], C['a3']],
                   legend=['Google ROAS', 'Instagram ROAS', 'TikTok ROAS'], fmtv=lambda v: f"{v:.0f}x",
                   line=[None if np.isnan(v) else v for v in roas_t.values], line_color=C['neg'])

g3 = stacked_bars([list(legit_ay.values/1e3), list(abuse_ay.values/1e3)], AY_AD,
                  [C['a4'], C['neg']], ['Yeni müşteri (amaçlanan)', 'Mevcut müşteri (istismar)'],
                  fmtv=lambda v: f"{v:.0f}K")

kat_ret = []
for kat in ['Ayakkabı','Mont','Aksesuar','Sırt Çantası','Kamp Ekipmanı','Termos ve Matara']:
    sd = m[m.kategori==kat].adet.sum()
    rt = iadm[iadm.kategori==kat].adet.sum()
    kat_ret.append((kat, rt/sd*100))
kat_ret.sort(key=lambda x: -x[1])
g4 = barh(kat_ret)

g5 = grouped_bars([list(pl.kargo/1e3), list(pl.alinan/1e3)], AY_AD, [C['neg'], C['a4']],
                  legend=['Kargo maliyeti (mağaza)', 'Müşteriden alınan kargo ücreti'],
                  fmtv=lambda v: f"{v:.0f}K")

g6 = grouped_bars([[v*100 for v in termos_pay.values]], AY_AD, [C['a2']],
                  legend=['Termos & Matara payı (ciro içinde, %)', 'Net brüt marj (%)'],
                  fmtv=lambda v: f"%{v:.0f}",
                  line=list(((1-pl.cogs/pl.ciro)*100).values), line_color=C['a1'])

# ================= HTML =================
def tl(x, dec=0): return fmt(x, dec) + ' TL'
kar_ay = [f"{AY_AD[i]}: {tl(pl.kar.iloc[i])}" for i in range(6)]

tablo_pl = '<table><tr><th></th>' + ''.join(f'<th>{a}</th>' for a in AY_AD) + '</tr>'
rows = [('Ciro (ödenen)', pl.ciro), ('İade düşümü', -pl.iade), ('Ürün maliyeti (net)', -pl.net_cogs),
        ('Kargo (net)', -(pl.kargo-pl.alinan)), ('Katkı payı', pl.katki),
        ('Reklam', -pl.reklam), ('Sabit giderler', -pl.sabit), ('Faaliyet kârı', pl.kar)]
for name, s in rows:
    cls = ' class="hl"' if name in ('Katkı payı','Faaliyet kârı') else ''
    tablo_pl += f'<tr{cls}><td>{name}</td>' + ''.join(
        f'<td{" class=neg" if v<0 else ""}>{fmt(v/1e3)}K</td>' for v in s.values) + '</tr>'
tablo_pl += '</table>'

tt_ay_tab = '<table><tr><th>TikTok</th><th>Mayıs</th><th>Haziran</th><th>Temmuz</th><th>Ağustos</th><th>Toplam</th></tr>'
tt_ay_tab += '<tr><td>Katkı payı</td>' + ''.join(f'<td>{fmt(tt_ay[a][0]/1e3)}K</td>' for a in AYLAR[2:]) + f'<td>{fmt(tt_katki/1e3)}K</td></tr>'
tt_ay_tab += '<tr><td>Reklam harcaması</td>' + ''.join(f'<td>{fmt(tt_ay[a][1]/1e3)}K</td>' for a in AYLAR[2:]) + f'<td>{fmt(tt_harc/1e3)}K</td></tr>'
tt_ay_tab += '<tr class="hl"><td>Net katkı</td>' + ''.join(f'<td class="neg">{fmt(tt_ay[a][2]/1e3)}K</td>' for a in AYLAR[2:]) + f'<td class="neg">{fmt(tt_net/1e3)}K</td></tr></table>'

RAPOR = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kuzey Rüzgarı — Zarar Analizi | Mart–Ağustos 2026</title>
<style>
  :root {{ --ink:#1a2233; --mut:#5b6472; --pos:#1e9e6a; --neg:#d64550; --bg:#f6f7f9; --card:#ffffff; --line:#e6e8ee; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
        font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; line-height:1.55; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:40px 20px 80px; }}
  header {{ border-bottom:3px solid var(--ink); padding-bottom:18px; margin-bottom:8px; }}
  h1 {{ font-size:28px; margin:0 0 6px; letter-spacing:-.02em; }}
  h2 {{ font-size:20px; margin:44px 0 10px; padding-top:22px; border-top:1px solid var(--line); letter-spacing:-.01em; }}
  h3 {{ font-size:16px; margin:22px 0 6px; }}
  .sub {{ color:var(--mut); font-size:14px; }}
  .ozet {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; margin:22px 0; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }}
  .kpi .v {{ font-size:24px; font-weight:700; letter-spacing:-.02em; }}
  .kpi .l {{ font-size:12.5px; color:var(--mut); margin-top:2px; }}
  .neg {{ color:var(--neg); }} .poz {{ color:var(--pos); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px 22px; margin:16px 0; }}
  .rank {{ display:flex; gap:14px; align-items:flex-start; }}
  .no {{ flex:0 0 34px; height:34px; border-radius:9px; background:var(--ink); color:#fff;
        display:flex; align-items:center; justify-content:center; font-weight:700; }}
  .etki {{ font-size:20px; font-weight:700; color:var(--neg); white-space:nowrap; }}
  .tag {{ display:inline-block; font-size:11.5px; font-weight:600; padding:2px 9px; border-radius:20px;
         background:#fdecef; color:var(--neg); margin-left:8px; vertical-align:2px; }}
  .ok {{ background:#e7f6ef; color:var(--pos); }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; margin:10px 0; }}
  th, td {{ padding:7px 9px; text-align:right; border-bottom:1px solid var(--line); }}
  th:first-child, td:first-child {{ text-align:left; }}
  th {{ color:var(--mut); font-weight:600; }}
  tr.hl td {{ font-weight:700; background:#fafbfc; }}
  svg {{ width:100%; height:auto; display:block; margin:6px 0 2px; }}
  .ax {{ font-size:11px; fill:var(--mut); font-family:inherit; }}
  .ax2 {{ font-size:12.5px; fill:var(--ink); font-family:inherit; }}
  .axv {{ font-size:12px; fill:var(--ink); font-weight:600; font-family:inherit; }}
  .lg {{ font-size:11.5px; fill:var(--mut); font-family:inherit; }}
  .cap {{ font-size:12.5px; color:var(--mut); margin:2px 0 0; }}
  ul {{ padding-left:20px; margin:8px 0; }} li {{ margin:5px 0; }}
  .uc {{ background:#fff8ec; border:1px solid #f5dfa8; border-radius:14px; padding:20px 22px; }}
  .uc .n {{ font-weight:700; }}
  footer {{ margin-top:50px; font-size:12px; color:var(--mut); border-top:1px solid var(--line); padding-top:14px; }}
  .vars {{ font-size:13.5px; }}
</style></head><body><div class="wrap">

<header>
  <h1>Kuzey Rüzgarı: Satışlar büyürken neden zarar ediyoruz?</h1>
  <div class="sub">Yönetim kurulu analiz raporu · Dönem: 1 Mart – 31 Ağustos 2026 · Hazırlanma: 21 Eylül 2026</div>
</header>

<div class="ozet">
  <div class="kpi"><div class="v poz">+25%</div><div class="l">Ciro artışı (Mart → Ağustos, {mfmt(pl.ciro.iloc[0])} → {mfmt(pl.ciro.iloc[-1])})</div></div>
  <div class="kpi"><div class="v neg">{mfmt(TOPLAM_ZARAR)} TL</div><div class="l">6 aylık toplam faaliyet kârı</div></div>
  <div class="kpi"><div class="v neg">{mfmt(pl.kar.iloc[-1])} TL</div><div class="l">Ağustos aylık zararı (gidişat hızı)</div></div>
  <div class="kpi"><div class="v">Nisan</div><div class="l">Son kârlı ay — Mayıs başabaş, Haziran'dan itibaren zarar</div></div>
</div>

<p><b>Tek cümlelik cevap:</b> Büyümenin kendisi kârlı değil; Mayıs ortasında aynı anda devreye giren üç karar —
başabaşın altında getirisi olan TikTok reklam seferberliği, herkese açık hale gelen %30 hoş geldin kuponu ve
koşulsuz bedava kargo — birim ekonomiyi bozdu; üzerine kronikleşmiş ayakkabı iade sorunu (%33) ve düşük marjlı
termos satışlarının payının üç katına çıkması eklendi. Şirket Mart–Nisan'da ayda ~270K TL kâr ederken
Ağustos'ta ayda {mfmt(pl.kar.iloc[-1])} TL zarar ediyor.</p>

<h2>Aylık kâr tablosu: kırılma Mayıs'ta</h2>
<div class="card">{g1}
<p class="cap">Ciro her ay artarken faaliyet kârı Haziran'dan itibaren negatife döndü ve her ay derinleşti.
İadeler sipariş ayına yazıldı; kâr = net ciro + kargo tahsilatı − ürün maliyeti (satılabilir iadeler düşülerek) − kargo − iade kargosu − reklam − sabit gider.</p>
{tablo_pl}</div>

<h2>Nedenler, kanıtları ve TL etkileri</h2>
<p>Aşağıdaki etkiler 6 aylık toplam, bağımsız (tek başına düzeltilseydi) tahminlerdir; nedenler kısmen iç içe
geçtiği için toplamları zararın kendisini aşar — sıralama ve öncelik için kullanılmalıdır.</p>

<div class="card"><div class="rank"><div class="no">1</div><div style="flex:1">
<h3 style="margin-top:2px">TikTok reklamları: getirisi maliyetinin altında <span class="tag">−{mfmt(tt_net)} TL / 4 ay</span></h3>
<p><b>Kanıt:</b> Mayıs'ta başlayan TikTok harcaması Ağustos'ta {kfmt(rek[rek.kanal=='tiktok'].groupby('ay').harcama.sum().iloc[-1])} TL/aya ulaştı
(toplam {mfmt(tt_harc)} TL, tüm reklam bütçesinin %{tt_harc/rek.harcama.sum()*100:.0f}'si). TikTok'tan atfedilen ciro {mfmt(tt_ciro)} TL ama bu
siparişlerin ürün, kargo ve iade maliyetleri düşüldüğünde katkı payı yalnız {kfmt(tt_katki)} TL (katkı marjı %{tt_katki/tt_ciro*100:.0f}).
<b>ROAS {tt_roas:.2f}x; başabaş için {tt_basabas:.1f}x gerekiyordu.</b> Yani TikTok'a verilen her 1 TL, maliyetlerden sonra ~{(tt_katki/tt_harc):.2f} TL geri getirdi.
Karşılaştırma: aynı dönemde Google {kfmt(g_net)} TL, Instagram {kfmt(i_net)} TL <i>net katkı</i> üretti — sorun reklamın kendisi değil, TikTok kanalı.</p>
{tt_ay_tab}
{g2}
{g2b}
<p class="cap">Sağdaki grafikte kırmızı çizgi TikTok ROAS: 2,2x'ten 1,4x'e düşüyor; harcama ise 7,6 kat arttı. Ölçek büyüdükçe verim düşüyor.</p>
</div><div class="etki">−{mfmt(tt_net)}</div></div></div>

<div class="card"><div class="rank"><div class="no">2</div><div style="flex:1">
<h3 style="margin-top:2px">HOSGELDIN30 kuponu istismarı: mevcut müşterilere %30 <span class="tag">−{mfmt(ABUSE_TOP)} TL / 6 ay</span></h3>
<p><b>Kanıt:</b> "İlk siparişe özel" olması gereken HOSGELDIN30 kodunu <b>mevcut müşteriler</b> Mart–Mayıs'ta ayda 2–12 siparişte kullanırken
Haziran'da 318, Temmuz'da 691, Ağustos'ta 925 siparişte kullandı. Mevcut müşterilere verilen indirim toplamı <b>{tl(ABUSE_TOP)}</b>
(495 müşteri kodu 2+ kez, 48'i 3+ kez kullandı). Patlama TikTok kampanyasının hemen ardından başlıyor; kod büyük olasılıkla
kupon sitelerine / sosyal medyaya sızdı. İndirim oranı ciroya oranla %4,7'den %10,5'e çıktı.</p>
<p><b>Ağır sonuç:</b> Marjı sadece %22 olan <b>Termos 1L</b> (1.190 TL fiyat / 928 TL maliyet) %30 kuponla 833 TL'ye satılınca
<b>maliyetin altında satış</b> oluştu: 1.304 satırda toplam {tl(ALTI_ZARAR)} doğrudan zarar (tamamı HOSGELDIN30'lu).</p>
{g3}
<p class="cap">Kırmızı dilim: kodun amaçlanmayan kullanımı (mevcut müşteriler). Haziran'da kontrolden çıkıyor.</p>
</div><div class="etki">−{mfmt(ABUSE_TOP)}</div></div></div>

<div class="card"><div class="rank"><div class="no">3</div><div style="flex:1">
<h3 style="margin-top:2px">Ayakkabıda %33 iade oranı: kronik ve pahalı <span class="tag">−{mfmt(AYAKKABI_ETKI)} TL / 6 ay</span></h3>
<p><b>Kanıt:</b> Satılan her 3 ayakkabıdan 1'i iade ediliyor (1.804 satış → 599 iade); diğer tüm kategoriler %{REF_ORAN*100:.1f} civarında.
İade nedenlerinde açık ara lider "beden uymadı" (518 adet, 1,37M TL'lik iade; 435'i ayakkabı). Kanaldan bağımsız
(%28–35 her kanalda yüksek) yani sorun reklam kitlesi değil, ürün/beden bilgisi. İade edilen ayakkabıların %{ns*100:.0f}'i
yeniden satılamıyor (giyildiği için stoğa dönemiyor).</p>
<p><b>Hesap:</b> Ayakkabı, diğer kategorilerin oranında iade alsaydı ~{excess:.0f} daha az iade olurdu. Fazladan her iade
~{fmt(birim_marj)} TL kaybedilen marj + {fmt(rk)} TL iade kargosu + %{ns*100:.0f} olasılıkla {fmt(birim_maliyet)} TL maliyet yazık olması demek
→ toplam <b>~{mfmt(AYAKKABI_ETKI)} TL</b>.</p>
{g4}
<p class="cap">Bu sorun 6 aydır var (Mart'tan beri yüksek); yeni değil ama büyüme ayakkabı hacmini de büyüttüğü için faturası şişiyor.</p>
</div><div class="etki">−{mfmt(AYAKKABI_ETKI)}</div></div></div>

<div class="card"><div class="rank"><div class="no">4</div><div style="flex:1">
<h3 style="margin-top:2px">Ürün miksi düşük marjlı termosa kaydı <span class="tag">−{mfmt(MIKS_ETKI)} TL / 5 ay</span></h3>
<p><b>Kanıt:</b> Termos &amp; Matara'nın ciro içindeki payı Mart'ta %{termos_pay.iloc[0]*100:.0f} iken Ağustos'ta %{termos_pay.iloc[-1]*100:.0f}.
Kategori marjları sabitken bu kayma tek başına ortalama ürün maliyet oranını %{base_ratio*100:.1f}'den %{mix_ratio.iloc[-1]*100:.1f}'e çıkardı.
Kupon ve TikTok'un ucuz ürün satışını pompalaması bu kaymanın bir kısmını açıklıyor (örtüşme notu: Termos 1L'nin maliyet altı satışı
2. maddede sayıldı) ama kayma organik kanalda da görülüyor; yani ayrıca bir fiyatlama/asortman kararı konusu.</p>
{g6}
<p class="cap">Mavi çizgi: indirimler dahil net brüt marj — %{((1-pl.cogs/pl.ciro).iloc[0]*100):.0f}'den %{((1-pl.cogs/pl.ciro).iloc[-1]*100):.0f}'e geriledi; düşüşün ~yarısı kupon, ~yarısı miks kaynaklı.</p>
</div><div class="etki">−{mfmt(MIKS_ETKI)}</div></div></div>

<div class="card"><div class="rank"><div class="no">5</div><div style="flex:1">
<h3 style="margin-top:2px">15 Mayıs'ta koşulsuz bedava kargo <span class="tag">−{mfmt(KARGO_ETKI)} TL / 3,5 ay</span></h3>
<p><b>Kanıt:</b> 15 Mayıs'a kadar 750 TL altı sepetlerden sabit 139 TL kargo ücreti alınıyordu (istisnasız: 557/557 sipariş).
O tarihte ücret tüm siparişler için sıfırlandı; kargo maliyeti ise sipariş başına ~121 TL ile sabit kaldı. Sonraki 3,5 ayda
750 TL altı {len(kucuk_post):,} siparişten alınamayan ücret <b>{tl(KARGO_ETKI)}</b>. Dolaylı etki daha büyük olabilir:
küçük sepetli siparişlerin payı %{pre_pay*100:.0f}'den %{post_pay*100:.0f}'e sıçradı (ortalama sepet 3.400 TL → 1.740 TL) —
bedava kargo, kargo maliyeti marjı yiyen mini siparişleri teşvik ediyor.</p>
{g5}
</div><div class="etki">−{mfmt(KARGO_ETKI)}</div></div></div>

<h2>Şüpheli görünüp suçsuz çıkanlar</h2>
<div class="card"><ul>
<li><b>Sabit giderler:</b> 6 ay boyunca kuruşu kuruşuna aynı (1,53M TL/ay). Artış yok, zararın sebebi olamaz.</li>
<li><b>Google ve Instagram reklamları:</b> Harcama ~2 kat arttı ama katkı payı bazında hâlâ kârlılar
(6 ayda Google {mfmt(g_net)} TL, Instagram {mfmt(i_net)} TL net katkı). Kesintiye değil, TikTok'a bakılmalı.</li>
<li><b>"Hasarlı geldi" iadeleri:</b> {tl(hasar)} tutarında ama oran dönem boyu stabil ve toplam iadenin ~%9'u; kırılmayı açıklamıyor.</li>
<li><b>BAHAR15 / KAMP10 kuponları:</b> Toplam {tl(diger_kupon)} indirim — HOSGELDIN30'un yanında cüzi.</li>
<li><b>Düşen ortalama sepet (3.408 → 1.737 TL):</b> Bağımsız bir neden değil; termos miksine kayışın, kupon istismarının ve
bedava kargonun şişirdiği mini siparişlerin <i>belirtisi</i>.</li>
<li><b>Mevsimsellik:</b> Kış ürünleri yazın satılıyor görünse de kategori marjları sabit; sorun ne sattığımız değil, hangi koşullarda sattığımız.</li>
</ul></div>

<h2>Yöntem ve varsayımlar</h2>
<div class="card vars"><ul>
<li>P&amp;L, sipariş ayı bazında kuruldu: iadeler (işlem tarihi Eylül'e sarkanlar dahil) ait oldukları siparişin ayına yazıldı.
Satılabilir iade ürün maliyeti geri alındı sayıldı; "yeniden satılamaz" iadelerde maliyet zarar yazıldı.</li>
<li>Kanal etkililiği, verideki son-tıklama atfına dayanır (siparişin <i>kanal</i> alanı). TikTok için ciro → katkı payı →
reklam düşümü sırasıyla hesaplandı; organik kayma (kanibalizasyon) ölçülemediği için TikTok'un gerçek etkisi muhtemelen daha da kötüdür.</li>
<li>Kupon istismarında "mevcut müşteri" = kodu ilk siparişi dışındaki bir siparişte kullanan müşteri. Bu müşterilerin
indirimsiz de alışveriş yapacağı varsayıldı (kupon olmasa sepeti terk edenler olabilir; bu durumda gerçek etki biraz düşer).</li>
<li>Ayakkabı iadesinin "fazla" kısmı, ayakkabı dışı kategorilerin ağırlıklı ortalama iade oranı (%{REF_ORAN*100:.1f}) referans alınarak hesaplandı.</li>
<li>Bedava kargonun doğrudan etkisi, eski kuralın (750 TL altı = 139 TL) 15 Mayıs sonrası siparişlere uygulanmasıyla bulundu;
davranışsal etki (mini sipariş patlaması) ayrıca ve tutucu biçimde sayılmadı.</li>
<li>Kargo maliyeti sipariş başına ~121 TL'de sabit kaldığı için kargo firması zammı bir neden olarak elendi.</li>
</ul></div>

<div class="uc"><h2 style="border:none;margin-top:0;padding-top:0">Yarın sabah ilk yapılacak üç şey</h2>
<ol>
<li><span class="n">TikTok reklamlarını duraklat.</span> Katkı bazında başabaş ROAS ~2,6x; kanal 1,4x'te. Durdurma anında
aylık ~{kfmt(-tt_ay['2026-08'][2])} TL kanamayı keser. Yeniden açılacaksa hedef: katkı bazlı ROAS ≥ 3x olan daraltılmış kampanyalar.</li>
<li><span class="n">HOSGELDIN30'u bugün iptal et, kodu yalnız ilk siparişle sınırlı tek kullanımlık yeni kodla değiştir.</span>
Mevcut müşterilere akan indirim Ağustos hızıyla ayda ~{kfmt(abuse_ay.iloc[-1])} TL. Aynı anda Termos 1L gibi düşük marjlı
ürünleri kupon kapsamından çıkar (maliyet altı satışı bitirir).</li>
<li><span class="n">Ayakkabıda iade seferberliği başlat ve 750 TL altına kargo ücretini geri getir.</span>
Beden tablosunu ölçülerle netleştir, "beden uymadı" iadelerini ürün bazında izle (en çok hangi modelden?), iade edilen
ayakkabının satılabilirlik kontrolünü sıkılaştır. Eski kargo kuralının dönüşü ayda ~{kfmt(KARGO_ETKI/3.5)} TL getirir;
eşiği 1.000 TL'ye çıkarmak mini siparişleri de disipline eder.</li>
</ol>
<p class="cap" style="margin-top:10px">Bu üç adımın Ağustos gidişat hızındaki toplam etkisi ayda ~1,2–1,4M TL; şirketi tek başına
başabaşa yaklaştırır. Termos miks kayması ve fiyatlama ise bir sonraki haftanın gündemi olmalı.</p></div>

<footer>Kaynak: veri/ klasöründeki 5 CSV (21.211 sipariş satırı, 1.525 iade, 1.156 reklam günü). Analiz: analiz.py ·
Tüm tutarlar TL · Grafikler rapora gömülüdür, dosya çevrimdışı açılabilir.</footer>
</div></body></html>"""

with open('rapor.html', 'w', encoding='utf-8') as f:
    f.write(RAPOR)

print("=== ÖZET ===")
print(f"6 aylık faaliyet kârı: {TOPLAM_ZARAR:,.0f} TL")
print(f"1) TikTok net: {tt_net:,.0f} TL (ROAS {tt_roas:.2f}, başabaş {tt_basabas:.2f})")
print(f"2) Kupon istismarı: {ABUSE_TOP:,.0f} TL (maliyet altı satış dahil: {ALTI_ZARAR:,.0f})")
print(f"3) Ayakkabı fazla iade: {AYAKKABI_ETKI:,.0f} TL (oran %{AY_ORAN*100:.1f} vs %{REF_ORAN*100:.1f})")
print(f"4) Miks kayması: {MIKS_ETKI:,.0f} TL")
print(f"5) Bedava kargo: {KARGO_ETKI:,.0f} TL")
print("rapor.html yazıldı")
