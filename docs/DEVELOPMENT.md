# Geliştirme ve sprint kapatma düzeni

Kullanıcı her sprintin sonunda yapılan işlemleri ve nedenlerini açıklayan metin raporu ister. Çalışan kod, gerekli testler ve anlaşılabilir sonuç raporu aynı teslimin parçalarıdır.

## Her sprintte izlenecek sıra

1. Mevcut çalışma ve Git durumunu kontrol et; başka çalışmaları koru.
2. Sprint hedefini ve somut kabul ölçütlerini yaz.
3. Değişikliği modüler olarak uygula; gereksiz servis ve bağımlılık ekleme.
4. Her uygulama aşamasından sonra değişen davranışı, hata yollarını ve ilgili önceki davranışları test et; bulunan hataları sonraki aşamaya geçmeden gider.
5. `python scripts/check.py` kalite kapısını çalıştır. Hata varsa düzelt ve ilgili kontrolleri tekrarla.
6. Paketleme veya giriş noktası değiştiyse kurulu paket/CLI'yi kaynak klasörünün dışında doğrula.
7. Sprint raporunu tamamla ve kullanıcıya metin olarak özetle. Açık engeller varsa sprinti tamamlandı sayma.

## Kalite kapısı

Kod denetimi ve biçim kontrolü için Ruff; birim, entegrasyon ve uçtan uca testler için pytest kullanılır. Dallanma kapsamı da ölçülür; toplam eşik %90'dır. Bu eşik tek başına doğruluk kanıtı değildir. Testler yalnızca satır kapsamını artırmak için eklenmez; gereksinim, hata yolu veya regresyonu doğrulamalıdır.

Test oturumunda ağ bağlantıları engellenir. Beklenen fiziksel değerler için bağımsız elle hesaplanmış örnekler; güvenli yürütme için bozuk çıktı ve yetkisiz araç çağrıları kullanılır. Akademik başarı ölçümleri yazılım testlerinden ayrı raporlanır.

## Sprint raporunun içeriği

- Hedef ve kabul edilen kapsam.
- Nelerin değiştiği ve her değişikliğin gerekçesi.
- Çalıştırılan testler ve gerçek sonuçları; çalıştırılmayan kontroller.
- Kullanılabilir demo ve yeniden çalıştırma komutları.
- Bilinen sınırlamalar ve kapsam dışında bırakılan işler.
- Önceki çalışmanın korunma durumu ve sonraki adım.

Bir özelliğin yalnızca katalogda bulunması, test dosyasının var olması veya planlanması tamamlanmış olduğu anlamına gelmez. Kayıtlı, uygulanmış ve olay sırasında gerçekten çalıştırılmış ajan sayıları ayrı belirtilir.

## Panel içeren sprintlerde ek kapı

`web` içinde `npm ci` sonrasında `.venv/bin/python scripts/check.py --panel`, Python kontrollerine ek olarak ön yüz biçim/tip/test/derleme kontrollerini çalıştırır. API sözleşmesi değişirse önce `npm run types` kullanılır. Üretim derlemesi Python paketine dahil edildiği için kurulu paketin statik dosyaları ve gerçek HTTP kontrolü ayrıca doğrulanır. Yerel tarayıcı testleri ayrı test yapılandırması/veritabanıyla yapılır; üretim anahtarları testlere veya kaynak koduna yazılmaz.
