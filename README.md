# Namaz Vakti Telegram Botu

## Kurulum ve çalıştırma

Python 3.10 veya üzeri gerekir. Proje bağımlılıklarını yükle:

```powershell
python -m pip install -r requirements.txt
```

BotFather'dan yeni bir bot tokenı alıp `TELEBOT_TOKEN` ortam değişkenine ata ve botu başlat:

```powershell
$env:TELEBOT_TOKEN = "BOTFATHER_TOKEN"
python bot.py
```

Tokenı kaynak koduna veya paylaşılan dosyalara ekleme. Önceki sürümde token kaynak kodunda bulunuyordu; o tokenı BotFather üzerinden iptal edip yenisini kullan.

Botta `/start` karşılama mesajını, `/vakitler` konum paylaşma düğmesini, `/yardim` komut listesini ve `/iptal` klavyeyi kapatma seçeneğini gösterir. Bot ayrıca Telegram komut menüsünü başlatma sırasında kaydeder; konumlar ve kullanıcı mesajları dosyaya kaydedilmez.

## Namaz vakti API protokolü

`prayer_api.py` içindeki `PrayerTimesProvider`, bot ile namaz vakti sağlayıcısı arasındaki Python `Protocol` arayüzüdür. Sağlayıcı, `get_timings(latitude, longitude)` metodundan namaz adı ve saatini eşleyen bir `Mapping[str, str]` döndürür. HTTP katmanı `PrayerTimesHTTPSession` ve `PrayerTimesResponse` protokolleriyle tanımlanmıştır; böylece istemci gerçek `requests` modülüyle veya testlerde sahte bir oturumla kullanılabilir.

`AladhanPrayerTimesClient` bu arayüzü Aladhan API'sine şu istekle uygular:

- `GET https://api.aladhan.com/v1/timings/{DD-MM-YYYY}`
- Sorgu parametreleri: `latitude`, `longitude`, `method=2`
- Yanıt: `data.timings` alanındaki namaz adı/saat eşlemesi

Enlem/boylam aralığı doğrulanır ve gerekli vakit alanları kontrol edilir. İstek hataları, başarısız API yanıtları ve beklenmeyen yanıt biçimleri `PrayerTimesAPIError` olarak bildirilir. Testleri çalıştırmak için:

```powershell
python -m unittest discover -v
```
