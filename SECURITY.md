# Güvenlik politikası

## Desteklenen kapsam

0.7.x araştırma prototipi yalnızca yerel, sentetik veriyle kullanım içindir.
API varsayılan olarak `127.0.0.1` üzerinde çalışır. İnternete veya tesis ağına
açık üretim servisi olarak doğrulanmamıştır. Gerçek PLC adaptörü ve fiziksel
komut yürütme bulunmaz. İşletim sistemi süreç izolasyonu, SSO ve tesis güvenlik
değerlendirmesi tamamlanmış özellikler değildir.

## Açık bildirme

Bir açık, sızmış anahtar veya gerçek veri fark ederseniz içeriği issue, PR,
commit veya ekran görüntüsüne koymayın. Önce organizasyon sahibi `mirackeser`
ile mevcut özel iletişim kanalınızdan temas kurun. Özel güvenlik bildirimi
GitHub üzerinde etkinse Security → Report a vulnerability kullanılabilir;
bu dosyanın varlığı o özelliğin etkin olduğunu göstermez.

Etkilenen sürümü, tekrar üretme adımlarını ve beklenen/gerçekleşen davranışı
gizli değerleri çıkartarak bildirin. Değerlendirme tamamlanmadan yayımlamayın.

## Sızıntı müdahalesi

1. Gerçek bir anahtar sızmışsa ilgili hizmette iptal edin/yenileyin.
2. Erişim ve kullanım kayıtlarını kontrol edip etkiyi belirleyin.
3. İçeriği güncel ağaçtan kaldırın; geçmişte bulunuyorsa koordineli geçmiş
   temizliği planlayın. Dosyayı son committen silmek eski commitleri temizlemez.
4. Taramayı tekrar çalıştırın ve sonucu özel olarak kaydedin.

## Geliştirme önlemleri

İki aşamalı doğrulama, kişiye özel erişim, en az yetki, private depo,
kilitli bağımlılıklar, salt okuma izinli CI ve PR incelemesi hedef düzendir.
Bağımlılık taraması ve gizli bilgi taraması bilinen örüntülerle sınırlıdır;
başarılı testler veya boş tarama raporu güvenlik garantisi değildir.
