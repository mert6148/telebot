import telebot
import requests
from datetime import datetime

bot = telebot.TeleBot("7983937405:AAGJyxDQ0KCgP9AABhWg3V_7pcsGNqLFktQ")  # Botunuzun token'ını buraya girin

# Botun mesaj alması durumunda yapılacak işlemler
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Mesajları dosyaya kaydet
    with open("message_log.txt", "a") as message_log_file:
        log_text = f"Kullanıcı adı: {message.from_user.username}\n"
        log_text += f"Id: {message.chat.id}\n"
        log_text += f"Kullandığı komut: {message.text}\n"
        log_text += f"Mesaj tarih saati: {datetime.now().strftime('%d.%m.%Y - %H:%M')}\n"
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude
            city_name = get_city_name(latitude, longitude)
            log_text += f"Konum bilgisi: {city_name}\n"
        log_text += "\n"
        message_log_file.write(log_text)

    # Mesajı işle
    bot.reply_to(message, "⏳ Lütfen bekleyin...")

    # Komutlara göre işlem yap
    if message.text.lower() == '/start':
        send_welcome(message)
    elif message.text.lower() == '/vakitler':
        get_location(message)

# Kullanıcıya hoş geldiniz mesajı gönderen fonksiyon
def send_welcome(message):
    bot.reply_to(message, "👋 Es Selamun aleyküm dostlarım,\nNamaz vakti botuna hoş geldiniz.📿\n📖 Namaz vakitlerini görmek için /vakitler komutunu kullanabilirsiniz.")

# Kullanıcının konumunu alıp namaz vakitlerini gösteren fonksiyon
def get_location(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    item = telebot.types.KeyboardButton('👳‍♂ Konum Paylaş', request_location=True)
    markup.add(item)
    msg = bot.reply_to(message, "🧕 Lütfen konumunuzu paylaşın:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_location)

def process_location(message):
    try:
        latitude = message.location.latitude
        longitude = message.location.longitude

        # Mesajları dosyaya kaydet
        with open("message_log.txt", "a") as message_log_file:
            log_text = f"{datetime.now()} - {message.chat.id} - {message.from_user.username}: Konum - ({latitude}, {longitude})\n"
            message_log_file.write(log_text)

        url = f"https://api.aladhan.com/v1/calendar?latitude={latitude}&longitude={longitude}&method=2"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            today = datetime.now().strftime("%Y-%m-%d")
            timings = data['data'][0]['timings']

            translated_timings = {
                'Fajr': '☪ İmsak',
                'Sunrise': '☪ Güneş Doğuşu',
                'Dhuhr': '☪ Öğle',
                'Asr': '☪ İkindi',
                'Sunset': '☪ Güneş Batışı',
                'Maghrib': '☪ Akşam',
                'Isha': '☪ Yatsı',
                'Imsak': '☪ İmsak',
                'Midnight': '☪ Geceyarısı',
                'Firstthird': '☪ Üçte Bir',
                'Lastthird': '☪ Son Üçte Bir'
            }

            message_text = "🕌 Bugünkü namaz vakitleri:\n\n"
            for time, value in timings.items():
                translated_time = translated_timings.get(time, time)
                message_text += f"{translated_time}: {value}\n"

            bot.send_message(message.chat.id, message_text)
        else:
            bot.reply_to(message, "❌ Namaz vakitleri alınamıyor. Lütfen daha sonra tekrar deneyin.")
    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu: {e}")

def get_city_name(latitude, longitude):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()