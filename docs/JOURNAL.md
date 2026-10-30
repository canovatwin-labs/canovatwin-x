# Çevrimdışı akış olay günlüğü

`StreamJournal`, sentetik telemetri toplayıcısının işlemlerini ayrı bir SQLite
dosyasına yazar. `append`, `drain`, `disconnect` ve `reconnect` olayları
işlemseldir: önce kopya akışta doğrulanır, veritabanı işlemi başarıyla
tamamlanınca canlı bellek durumu değiştirilir. Bu nedenle reddedilen ölçüm veya
disk yazma hatası akışı kısmen ilerletmez.

Her olay sıralı numara, önceki hash ve içerik hash'i taşır. Açılışta tüm zincir,
son kayıt başlığı, sayı, şema ve yapılandırma kontrol edilir; olaylar alan
kurallarından tekrar geçirilerek bekleyen tampon, son 600 kesinleşmiş ölçüm,
zaman eşiği ve bağlantı durumu kurulur. Bozuk günlük sessizce atlanmaz.
Başka bir yazıcı aynı dosyayı değiştirdiyse eski tutamak açık hatayla durur;
çağıran yeni tutamak açıp yeniden okumalıdır.

Günlük **10.000 olayla sınırlıdır**; sınırda sessiz silme yapılmaz. Bu, kısa
çevrimdışı deneyler içindir. Üretim için arşiv/rotasyon, tek yazıcı hizmeti ve
uzun süreli saklama tasarlanıp ayrıca test edilmelidir. Hash zinciri yanlışlıkla
bozulmayı bulur; dosyayı ve hash'leri birlikte değiştirebilen saldırgana karşı
kimlik doğrulaması sağlamaz. Ayrı PLC veya ağ bağlantısı içermez.
