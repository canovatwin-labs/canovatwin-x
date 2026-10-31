# CanovaTwin X — Sprint 12 sonuç raporu

**31 Ekim 2026 · Uygulama 0.13.0 · Analiz motoru 0.4.0**

## Yapılan iş ve gerekçe

Sentetik değerlendirmeden gerçek ölçüme geçişi somutlaştırmak için yayıncı
sürümü ve CC BY 4.0 lisansı kayıtlı AAU Zenodo v5 sunucu odası verisinin iki
küçük yardımcı CSV'sine çevrimdışı adaptör eklendi. Ham dosyalar depoya
konmadı. Yayıncı MD5 değerleri doğrulanıyor; yerel SHA-256 ve açık kaynak,
lisans, saat dilimi varsayımı raporlanıyor.

İki sıcaklık sensörü yalnızca aynı zaman damgasında gözlendiyse eşleniyor.
Zaman ayrımlı train/validation/test kümeleri arasında bir saat embargo var.
Önce katı dış veri doğrulama, sonra yalnızca test kümesinde altı uzmanlı keşif
incelemesi çalışıyor. Eksik sensörler ve bilinmeyen arıza etiketleri korunuyor.

## Gerçek veri sonucu

1.521 eşzamanlı çift bulundu; 10'u sınır embargosu için dışarıda bırakıldı.
503/503/505 satırlık ayrık kümeler doğrulandı. Medyan örnekleme 900 saniye;
train ve validation kümelerinde birer zaman boşluğu var. İki kanalda eksik ve
aralık dışı değer sayısı sıfır. Test incelemesi `insufficient_data` ve zorunlu
insan incelemesi üretti. Bu sonuç beklenen güvenli çekimserliktir, arıza teşhis
başarısı değildir. Ayrıntı: [AAU vaka çalışması](AAU_CASE_STUDY.md).

## Testler ve açık sınırlar

Dokuz çevrimdışı test tam dönüşümü, birebir eşleşmeyi, embargo ve bölme
ayrımını, kaynak checksum hatasını, saat dilimi zorunluluğunu ve var olan çıktıyı
korumayı denetler. Yerelde **549 Python testi**, **39 panel testi** geçti;
Python satır+dal kapsamı **%95,58**. Ruff, Prettier, TypeScript, panel derlemesi,
`actionlint` ve `gitleaks` temiz. Kaynak paketi ve 0.13.0 wheel oluşturuldu;
panel ve MIT lisansı pakette doğrulandı. Temiz kurulan wheel ile gerçek AAU
dosyaları tekrar işlendi: 1.521 eşleşme, 503/503/505 satır ve güvenli
çekimserlik aynı kaldı. Aynı pakette veri/akış/günlük kontrolleri ve gerçek
yerel HTTP üzerinde 22 referans + 33 dinamik birleşim, yetki, replay ve dört
eşzamanlı yazma geçti. GitHub CI sonucu ayrıca PR'da doğrulanır.

Kaynak CSV saat dilimi belirtilmemiştir; `+02:00` koşum varsayımıdır. Veri
etiketsiz ve iki kanallıdır. Gerçek PLC, şirket verisi, kalibrasyon, diğer 24
uzman ve bağımsız teşhis performans ölçümü hâlâ açık iş olarak kalır.
