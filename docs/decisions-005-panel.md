# Karar 005 — Yerel panel ve tek servis

React + TypeScript, önceki yol haritasındaki web paneli seçimini uygular. Vite yalnızca geliştirme/derleme aracıdır. Derlenmiş dosyalar Python paketinde ve aynı kaynak altında sunulur; çalışma için Node servisi veya CORS yapılandırması gerekmez. Hash tabanlı gezinme, sunucuda genel dosya/SPA fallback açmadan tarayıcı geri/ileri gezinmesini sağlar.

Kaynaklar: [Vite statik dağıtım ve base yolu](https://vite.dev/guide/static-deploy), [React Effect temizliği ve yarış durumları](https://react.dev/learn/synchronizing-with-effects). Resmî dokümanlardan çıkan uygulama kararı: veri okuyan Effect sonuçları temizlenince eski ekrana yazılmaz; POST işlemleri kullanıcı olayıyla başlar ve otomatik tekrar edilmez.

## Sözleşmeler

FastAPI OpenAPI şeması çevrimdışı dışa verilir; openapi-typescript ile türler üretilir. Python testi, kaydedilen şemayı gerçek API ile karşılaştırır. Arayüz testlerinin veri şekilleri hayalî değildir: geçici gerçek API üzerinden üretilen üç sentetik kayıt, Python sözleşmeleriyle tekrar doğrulanır.

## Oturum ve sınırlar

Yeni `/api/v1/session` okuma/yazma rolünü sunucudan döndürür. İstemci tahmin ederek yetki belirlemez. Anahtar yalnızca oturum kapsamlı istemcide kalır; kapatma bekleyen istekleri iptal eder ve geç yanıtı yok sayar. Sunucu yetki kontrolleri her istek için korunur. Tarayıcı yenilemesinden sonra tekrar bağlantı gerekir. Kurumsal kişisel kimlik/SSO uygulanmadı.

## Ölçüm anlamı

Grafik gerçek örnek zamanlarını kullanır; eksik değer sıfır değildir. Verilen örnekleme aralığının 1,5 katını aşan boşluklarda çizgi kesilir. Grafik genişliğine göre koordinat alanı yeniden hesaplanır; dar ekranda eksen yazıları küçültülmez. Tablo sayısal alternatif sunar.

Motor sürümü 0.4.0 korunur; uygulama 0.6.0 olur. Sunum/HTTP değişikliği, saklanan analizlerin algoritmasını değiştirmez. 12 uygulanmış uzman kapasitesi ve olayda çalışmış adım sayısı ayrı bilgiler olarak gösterilir.

## Tekrarlanan paket derlemesi

Hash'li ön yüz dosyaları değişince setuptools'un önceki `build/lib` kopyası eski dosyaları taşıyabiliyordu. `build_py` alt sınıfı yalnızca üretilmiş panel kopyasını her gerçek derlemede yeniden oluşturur; kaynak veya özel yapılandırma silinmez. [Setuptools komut özelleştirme rehberi](https://setuptools.pypa.io/en/stable/userguide/extension.html) bu uzatma noktasını tanımlar. `setup.py` doğrudan çalıştırılmaz; PEP517/uv derlemesi kullanılır. Wheel/source dosyalarının birebir karşılaştırılması bu hatanın tekrarını yakalar.
