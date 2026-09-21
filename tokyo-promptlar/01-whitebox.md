Seninle adım adım bir Three.js sahnesi kuracağız: gece, yağmurlu bir Tokyo ara sokağı. İçinde yürüyebildiğim, sinematik bir yer olsun.

Bu ilk adımda sadece white-box istiyorum: her şey tek tip mat gri, clay render gibi. Materyal, neon, yağmur yok. Amaç sokağın kompozisyonunu ve ölçeğini oturtmak.

Sokağın karakterine sen karar ver: binaların ritmi, tabela yerleri, köşedeki detaylar, sokağın nereye açıldığı. Düz bir kutu koridoru olmasın; içinde yürüyünce gerçek bir yer gibi hissettirsin.

Sabit kurallar:
- Tek dosya: index.html. Three.js CDN'den, sabit sürüm. Çift tıklayınca açılsın; build ya da server yok.
- WASD + fareyle yürüyebileyim, duvarlardan geçmeyeyim.
- Sol üstte küçük bir overlay: FPS, frame süresi (ms), draw call, üçgen sayısı.
- Sonraki adımlarda materyal, tabela, ıslak zemin ve yağmur ekleyeceğiz; kodu buna göre kur.

Önce kısaca planını anlat, sonra yap. Bitince tarayıcıda açıp kontrol et ve index.html'in kopyasını asamalar/01-whitebox.html olarak kaydet.
