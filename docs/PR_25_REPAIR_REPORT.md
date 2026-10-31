# PR 25 uyumluluk düzeltmesi — 31 Ekim 2026

İlk hata, `@vitejs/plugin-react` 6.1.2'nin Vite `^8.0.0` istemesine rağmen
projenin Vite 7 kullanmasıydı. Dolayısıyla `npm ci` peer bağımlılık çözümünde
duruyor, üç Python sürümündeki işlerin hiçbiri test aşamasına ulaşamıyordu.

Güncel `main` değişiklikleri korundu; React eklentisi 6.1.2 ile Vite 8.3.5
birlikte yükseltildi. Kilit dosyası normal bağımlılık çözümüyle yeniden üretildi.
Peer denetimini atlama, zorla kurulum veya güvenlik eşiğini düşürme uygulanmadı.
Vite/React eklentisi gelecekte aynı Dependabot grubunda değerlendirilecek.

Temiz `npm ci`, OpenAPI tip üretimi, TypeScript, Prettier, **39 panel testi** ve
Vite 8 üretim derlemesi geçti. **549 Python testi**, **%95,58 kapsam**; tam npm
audit **sıfır bulgu**. Kaynak ve wheel paketleri oluşturuldu. Wheel'deki dört
panel dosyası kaynakla birebir eşleşiyor; eski dosya artığı yok, MIT lisansı
korunuyor. Temiz ortama kurulan wheel üzerinde gerçek loopback HTTP kabul
testi ayrıca çalıştırıldı. Son commitin Linux CI sonuçları PR'da izlenir.

Bu bakım değişikliği panelin paketleme aracını günceller; analiz motorunun
0.4.0 sürümünü veya arıza kurallarını değiştirmez. Aktarım laboratuvarının
geliştirme dalındaki değişiklikler bu düzeltmeye katılmadı.
