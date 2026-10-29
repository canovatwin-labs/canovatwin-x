# Sprint 6 — Dinamik simülasyon ve yoğun operatör paneli

Amaç: tek bölgeli sentetik modelde değişken iş yükü, ortam etkisi ve ekipman gecikmesini görünür kılmak; panel alanını ölçüm ve senaryo içeriğiyle değerlendirmek.

Kabul ölçütleri:
- Önceki referans üretici ve kayıtların yeniden analizi korunur.
- İsteğe bağlı dinamik üretici: üç iş yükü profili, ayarlanabilir yük/ortam/fan tepkisi, kademeli arızalar, soğutma gecikmesi ve sınırlı ölçüm gürültüsü. Deterministik tohum ve enerji dengesi test edilir.
- Üretim ayarları, senaryo ve üretici sürümü ajan girdilerinden ayrı kayıt metadatasında saklanır. Yeniden analiz bu metadatayı korur.
- Panel: düzenlenebilir çalışma koşulları, senaryo açıklaması ve zaman çizelgesi, ölçüme dayalı özet/topoloji ve sıcaklık/güç/fan grafikleri; mevcut yetki ve kayıt akışları korunur.
- Geriye uyumluluk, tüm senaryolar, hatalı giriş, yetkilendirme, tekrar oynatma, UI etkileşimleri, paket ve gerçek HTTP doğrulanır. Masaüstü/mobil görsel kontrol yapılır.

Sınır: saha kalibrasyonu, CFD, çok bölge, gerçek PLC ve yeni uzman aktivasyonu bu sprintte yoktur. Değişken sentetik veri, fiziksel doğruluğun saha kanıtı değildir. Tanı motoru değiştirilmediğinden motor sürümü korunur; uygulama 0.7.0 olur.
