# Avenox: Kimi K3 Notları

**Kimi K3'e altı iş verdim: biri adım adım, beşi tek promptla. Bu repo o videonun bütün malzemesi: promptlar, test verileri ve Kimi'nin ürettiği çıktılar, olduğu gibi.**

Bu video Kimi iş birliğiyle hazırlandı. Promptları, testleri ve değerlendirmeyi ben seçtim; çıktılara elle dokunulmadı. Beğenmediğim yerler de burada duruyor.

## Nasıl kullanırsın

Çıktıların hepsi tek dosyalık HTML. Repoyu indir, `index.html` dosyasına çift tıkla, tarayıcıda açılır. Kurulum, build, sunucu yok.

Kendi modelinle denemek istersen ilgili `PROMPT.md` dosyasını olduğu gibi kopyala, boş bir klasörde modeline ver ve sonucu buradakiyle karşılaştır.

## Ana iş: yağmurlu Tokyo sokağı (adım adım)

Gece, yağmurlu, içinde yürünebilen bir Three.js sahnesi. Tek promptta değil, dört adımda kuruldu. Her adımın sonundaki hali ayrı dosya olarak saklı; sahnenin gri kutulardan finale nasıl geldiğini sırayla açıp görebilirsin.

| Adım | Prompt | O adımın çıktısı |
|---|---|---|
| 1. White-box | [01-whitebox.md](tokyo-promptlar/01-whitebox.md) | [01-whitebox.html](tokyo/asamalar/01-whitebox.html) |
| 2. Materyal + neon | [02-materyal-neon.md](tokyo-promptlar/02-materyal-neon.md) | [02-materyal-neon.html](tokyo/asamalar/02-materyal-neon.html) |
| 3. Islak zemin + yağmur + atmosfer | [03-islak-zemin-yagmur-atmosfer.md](tokyo-promptlar/03-islak-zemin-yagmur-atmosfer.md) | [03-final-gorsel.html](tokyo/asamalar/03-final-gorsel.html) |
| 4. Optimizasyon + kamera turu | [04-optimizasyon-kamera-turu.md](tokyo-promptlar/04-optimizasyon-kamera-turu.md) | `tokyo/asamalar/` altında |

Son hal: [tokyo/index.html](tokyo/index.html). WASD ile yürü, fareyle bak.

Promptlar bilerek gevşek. Sabit kural az (tek dosya, çift tıkla açılsın, FPS göstergesi olsun); sokağın karakteri, tabelalarda ne yazacağı, yansımanın hangi yöntemle çözüleceği gibi kararlar modele bırakıldı. Görmek istediğim şey talimat takibi değil, zevk ve muhakemeydi.

## Tek atış testleri

Her biri tek prompt, düzeltme yok.

| # | Test | Neyi ölçüyor | Klasör |
|---|---|---|---|
| 1 | Gece çalışanlar için kahve markası landing page | Tasarım zevki, marka yaratma, responsive | [tek-atis/1-kahve-landing](tek-atis/1-kahve-landing) |
| 2 | Yerçekimi yönünü değiştirdiğin bulmaca oyunu | Oyun mantığı, bölüm tasarımı | [tek-atis/2-yercekimi-oyunu](tek-atis/2-yercekimi-oyunu) |
| 3 | Satışı büyüyen ama zarar eden mağazanın veri analizi | Akıl yürütme, sayısal doğruluk | [tek-atis/3-veri-analizi](tek-atis/3-veri-analizi) |
| 4 | Hatalı görev uygulamasında debugging | Mevcut kodu okuma, kök neden bulma | [tek-atis/4-debugging](tek-atis/4-debugging) |
| 5 | Etkileşimli 3D bisiklet aktarma sistemi | 3D + fizik tutarlılığı | [tek-atis/5-bisiklet](tek-atis/5-bisiklet) |

Notlar:

- **Veri analizi:** `veri/` altındaki beş CSV kurgusal ve bu test için üretildi (Kuzey Rüzgarı, 15.800 sipariş, altı ay). İçine bilerek dört zarar nedeni ve birkaç yanıltıcı iz gömüldü. Kimi'nin raporu: [rapor.html](tek-atis/3-veri-analizi/rapor.html).
- **Debugging:** klasördeki uygulama Kimi'nin düzelttiği haldir. Başlangıçta kullanıcı şikayeti olarak verilen yedi hata ve söylenmeyen bir bonus hata vardı; şikayet listesi [PROMPT.md](tek-atis/4-debugging/PROMPT.md) içinde.

## Skor

Süre, maliyet ve puanlar: [SKOR-TABLOSU.md](SKOR-TABLOSU.md).

## Bağlantılar

Projeler ve GitHub: https://github.com/avenoxai
Site: https://avenox.lol
X: https://x.com/Avenoxai
İletişim: taha@avenox.lol
