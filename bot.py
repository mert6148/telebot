import logging
import os
from typing import Mapping

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


def format_prayer_times(timings: Mapping[str, str]) -> str:
    lines = ["🕌 Bugünkü namaz vakitleri:"]
    lines.extend(
        f"{label}: {timings[key]}"
        for key, label in PRAYER_LABELS.items()
        if key in timings
    )
    return "\n".join(lines)


def create_bot(token: str, prayer_times: PrayerTimesProvider) -> telebot.TeleBot:
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Selam! Namaz vakitleri için /vakitler komutunu kullanabilirsin.\n"
            "Komutları görmek için /yardim yaz.",
        )

    @bot.message_handler(commands=["help", "yardim"])
    def handle_help(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Kullanılabilir komutlar:\n"
            "/start - Botu başlat\n"
            "/vakitler - Konumuna göre bugünün vakitleri\n"
            "/yardim - Bu yardım mesajı\n"
            "/iptal - Konum isteğini kapat",
        )

    @bot.message_handler(commands=["vakitler"])
    def handle_prayer_times_request(message: types.Message) -> None:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("📍 Konum paylaş", request_location=True))
        bot.reply_to(
            message,
            "Namaz vakitlerini hesaplamak için konumunu paylaş.\n"
            "İsteği sonlandırmak için /iptal yaz.",
            reply_markup=markup,
        )

    @bot.message_handler(commands=["cancel", "iptal"])
    def handle_cancel(message: types.Message) -> None:
        bot.reply_to(
            message,
            "İstek iptal edildi.",
            reply_markup=types.ReplyKeyboardRemove(),
        )

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

        bot.reply_to(
            message,
            format_prayer_times(timings),
            reply_markup=types.ReplyKeyboardRemove(),
        )

    @bot.message_handler(content_types=["text"])
    def handle_other_text(message: types.Message) -> None:
        bot.reply_to(
            message,
            "Bu mesajı anlayamadım. Komutlar için /yardim yazabilirsin.",
        )

    return bot


def register_commands(bot: telebot.TeleBot) -> None:
    bot.set_my_commands(
        [
            types.BotCommand("start", "Botu başlat"),
            types.BotCommand("vakitler", "Namaz vakitlerini göster"),
            types.BotCommand("yardim", "Yardım ve komutlar"),
            types.BotCommand("iptal", "Devam eden isteği iptal et"),
        ]
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("TELEBOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEBOT_TOKEN ortam değişkeni tanımlı değil. "
            "BotFather'dan aldığın tokenı bu değişkene ata."
        )

    bot = create_bot(token, AladhanPrayerTimesClient())
    register_commands(bot)
    LOGGER.info("Namaz vakti botu başlatılıyor.")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
