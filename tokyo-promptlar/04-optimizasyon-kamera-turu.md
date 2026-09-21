Son adım iki parça: önce performans, sonra video için kamera.

Parça 1, performans. Önce ölç, sonra dokun.
1. Sahneye bir benchmark ekle: 'B' tuşuyla 10 saniyelik sabit bir kamera rotasında ortalama ve en kötü %1 frame süresini ölçüp ekranda göstersin. Böylece öncesi ve sonrası aynı koşulda kıyaslanır. Makinem hızlıysa vsync yüzünden fark görünmeyebilir; bunu nasıl aşacağını sen çöz.
2. Mevcut durumu raporla: frame süresi, draw call, üçgen, texture ve render target belleği, ışık sayısı. Darboğaz nerede, neden?
3. Optimize et. Yöntem sende; her değişikliğin neden işe yaradığını bir cümleyle açıkla. Görsel kalite gözle fark edilir şekilde düşmesin; düşecekse bana seçenek sun.
4. Aynı benchmark ile öncesi/sonrası tablosu ver. Optimize halin kopyasını asamalar/04-optimize.html olarak kaydet.

Parça 2, video kapağı ve B-roll:
- 'C': sinematik kamera turu, 12-15 saniye. Rotayı ve ritmi sen tasarla; sahnenin en iyi karelerinden geçsin.
- Görünüm modları: '1' clay (white-box hali), '2' kuru materyalli, '3' final. Kamera turu her modda birebir aynı oynasın; kurguda üst üste bindirip sahnenin evrimini göstereceğim.
- 'P': 3840x2160 PNG ekran görüntüsü. 'H': overlay ve tüm arayüzü gizle/göster.

Bitince kontrol et, kopyasını asamalar/05-final.html olarak kaydet. En sonda öncesi/sonrası tablosunu bir kez daha yaz.
