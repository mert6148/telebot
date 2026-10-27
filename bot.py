import logging
import os

import telebot
from telebot import types

from prayer_api import AladhanPrayerTimesClient, PrayerTimesAPIError, PrayerTimesProvider

LOGGER = logging.getLogger(__name__)
PRAYER_LABELS = {
    "Fajr": "İmsak",
    "Sunrise": "Güneş",
    "Dhuhr": "Öğle",
    "Asr": "İkindi",
    "Maghrib": "Akşam",
    "Isha": "Yatsı",
}


def create_bot(token: str, prayer_times: PrayerTimesProvider) -> telebot.TeleBot:
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Selam! Namaz vakitlerini görmek için /vakitler komutunu kullanabilirsin.",
        )

    @bot.message_handler(commands=["vakitler"])
    def handle_prayer_times_request(message: types.Message) -> None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("Konum paylaş", request_location=True))
        bot.reply_to(message, "Namaz vakitleri için konumunu paylaş:", reply_markup=markup)

    @bot.message_handler(content_types=["location"])
    def handle_location(message: types.Message) -> None:
        if message.location is None:
            bot.reply_to(message, "Konum bilgisi alınamadı. Lütfen tekrar dene.")
            return

        try:
            timings = prayer_times.get_timings(
                message.location.latitude,
                message.location.longitude,
            )
        except PrayerTimesAPIError:
            LOGGER.exception("Namaz vakitleri API isteği başarısız oldu.")
            bot.reply_to(
                message,
                "Namaz vakitleri şu anda alınamıyor. Lütfen daha sonra tekrar dene.",
            )
            return

        lines = [
            "🕌 Bugünkü namaz vakitleri:",
            *(
                f"{PRAYER_LABELS[key]}: {timings[key]}"
                for key in PRAYER_LABELS
                if key in timings
            ),
        ]
        bot.reply_to(message, "\n".join(lines), reply_markup=types.ReplyKeyboardRemove())

    return bot


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("TELEBOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEBOT_TOKEN ortam değişkeni tanımlı değil. "
            "BotFather'dan aldığın tokenı bu değişkene ata."
        )

    bot = create_bot(token, AladhanPrayerTimesClient())
    LOGGER.info("Namaz vakti botu başlatılıyor.")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
