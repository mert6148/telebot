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

Botta `/start` karşılama mesajını, `/vakitler` ise konum paylaşma düğmesini gösterir.

## Namaz vakti API protokolü

`prayer_api.py` içindeki `PrayerTimesProvider`, bot ile namaz vakti sağlayıcısı arasındaki Python `Protocol` arayüzüdür. Sağlayıcı, `get_timings(latitude, longitude)` metodundan namaz adı ve saatini eşleyen bir `Mapping[str, str]` döndürür.

`AladhanPrayerTimesClient` bu arayüzü Aladhan API'sine şu istekle uygular:

- `GET https://api.aladhan.com/v1/timings/{DD-MM-YYYY}`
- Sorgu parametreleri: `latitude`, `longitude`, `method=2`
- Yanıt: `data.timings` alanındaki namaz adı/saat eşlemesi

İstek hataları, başarısız API yanıtları ve beklenmeyen yanıt biçimleri `PrayerTimesAPIError` olarak bildirilir.
