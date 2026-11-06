import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import telebot

from bot import create_bot, format_prayer_times, register_commands


class BotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = Mock()
        self.provider.get_timings.return_value = {
            "Fajr": "05:00",
            "Sunrise": "06:30",
            "Dhuhr": "12:15",
            "Asr": "15:30",
            "Maghrib": "18:00",
            "Isha": "19:30",
        }
        self.bot = create_bot("123:TEST", self.provider)

    def get_handler(self, filter_name: str, expected_value: object):
        for handler in self.bot.message_handlers:
            if handler["filters"].get(filter_name) == expected_value:
                return handler["function"]
        self.fail(f"No handler found for {filter_name}={expected_value!r}")

    def test_creates_telegram_bot(self) -> None:
        self.assertIsInstance(self.bot, telebot.TeleBot)

    def test_location_reply_formats_times_and_removes_keyboard(self) -> None:
        message = SimpleNamespace(
            chat=SimpleNamespace(id=123),
            location=SimpleNamespace(latitude=41.0, longitude=29.0),
        )
        handler = self.get_handler("content_types", ["location"])

        with patch.object(self.bot, "reply_to") as reply_to:
            handler(message)

        self.provider.get_timings.assert_called_once_with(41.0, 29.0)
        self.assertIn("İmsak: 05:00", reply_to.call_args.args[1])
        self.assertIsInstance(
            reply_to.call_args.kwargs["reply_markup"],
            telebot.types.ReplyKeyboardRemove,
        )

    def test_missing_location_does_not_call_provider(self) -> None:
        message = SimpleNamespace(chat=SimpleNamespace(id=123), location=None)
        handler = self.get_handler("content_types", ["location"])

        with patch.object(self.bot, "reply_to") as reply_to:
            handler(message)

        self.provider.get_timings.assert_not_called()
        self.assertIn("Konum", reply_to.call_args.args[1])

    def test_registers_telegram_commands(self) -> None:
        with patch.object(self.bot, "set_my_commands") as set_my_commands:
            register_commands(self.bot)

        names = [command.command for command in set_my_commands.call_args.args[0]]
        self.assertEqual(names, ["start", "vakitler", "yardim", "iptal"])

    def test_formatter_handles_only_supported_timings(self) -> None:
        self.assertEqual(
            format_prayer_times({"Fajr": "05:00", "Unknown": "00:00"}),
            "🕌 Bugünkü namaz vakitleri:\nİmsak: 05:00",
        )


if __name__ == "__main__":
    unittest.main()
