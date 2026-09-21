# Veri sözlüğü: Kuzey Rüzgarı

Dönem: 2026-03-01 ile 2026-08-31 arası siparişler. Para birimi TL. Dosyalar UTF-8, virgülle ayrılmış, ondalık ayracı nokta.

## urunler.csv
| Sütun | Anlam |
|---|---|
| urun_id | Ürün kimliği |
| urun_adi | Ürün adı |
| kategori | Ürün kategorisi |
| liste_fiyati | Birim satış fiyatı (TL) |
| birim_maliyet | Birim ürün maliyeti (TL) |

## siparisler.csv
Her satır bir siparişteki bir ürün kalemidir; bir sipariş birden fazla satırdan oluşabilir.

| Sütun | Anlam |
|---|---|
| siparis_id | Sipariş kimliği |
| tarih | Sipariş tarihi |
| musteri_id | Müşteri kimliği |
| urun_id | Ürün kimliği |
| adet | Adet |
| liste_fiyati | Birim liste fiyatı (TL) |
| kupon_kodu | Kullanılan kupon kodu, yoksa boş |
| indirim_tutari | Bu satıra uygulanan indirim (TL) |
| odenen_tutar | Müşterinin bu satır için ödediği tutar (TL) |
| kanal | Siparişin geldiği kanal |
| bolge | Teslimat bölgesi |
| musteriden_alinan_kargo | Müşteriden tahsil edilen kargo ücreti (TL). Sipariş düzeyindedir, yalnız siparişin ilk satırında yazar |
| kargo_maliyeti | Mağazanın kargo firmasına ödediği tutar (TL). Sipariş düzeyindedir, yalnız siparişin ilk satırında yazar |

## iadeler.csv
| Sütun | Anlam |
|---|---|
| siparis_id | İade edilen siparişin kimliği |
| urun_id | İade edilen ürün |
| adet | İade edilen adet |
| iade_tarihi | İadenin işlendiği tarih |
| neden | Müşterinin belirttiği iade nedeni |
| iade_edilen_tutar | Müşteriye geri ödenen tutar (TL) |
| iade_kargo_maliyeti | İade kargosunun mağazaya maliyeti (TL) |
| yeniden_satilabilir | Ürün tekrar stoğa alınabildi mi (evet / hayır) |

## reklam_harcamalari.csv
| Sütun | Anlam |
|---|---|
| tarih | Gün |
| kanal | Reklam kanalı |
| kampanya | Kampanya adı |
| harcama | Günlük harcama (TL) |
| tiklama | Günlük tıklama sayısı |

## sabit_giderler.csv
| Sütun | Anlam |
|---|---|
| ay | Ay (YYYY-AA) |
| kalem | Gider kalemi |
| tutar | Aylık tutar (TL) |
