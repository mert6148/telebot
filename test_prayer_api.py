import unittest
from unittest.mock import Mock

import requests

from prayer_api import AladhanPrayerTimesClient, PrayerTimesAPIError


class AladhanPrayerTimesClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.response = Mock()
        self.response.json.return_value = {
            "code": 200,
            "data": {
                "timings": {
                    "Fajr": "05:00",
                    "Sunrise": "06:30",
                    "Dhuhr": "12:15",
                    "Asr": "15:30",
                    "Maghrib": "18:00",
                    "Isha": "19:30",
                }
            },
        }
        self.session = Mock()
        self.session.get.return_value = self.response
        self.client = AladhanPrayerTimesClient(self.session)

    def test_requests_timings_and_returns_api_data(self) -> None:
        timings = self.client.get_timings(41.0, 29.0)

        self.assertEqual(timings["Fajr"], "05:00")
        self.session.get.assert_called_once()
        self.assertEqual(
            self.session.get.call_args.kwargs["params"],
            {"latitude": 41.0, "longitude": 29.0, "method": 2},
        )
        self.response.raise_for_status.assert_called_once()

    def test_rejects_coordinates_outside_valid_ranges(self) -> None:
        for latitude, longitude in ((91.0, 0.0), (0.0, 181.0)):
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(PrayerTimesAPIError):
                    self.client.get_timings(latitude, longitude)

        self.session.get.assert_not_called()

    def test_rejects_incomplete_api_response(self) -> None:
        self.response.json.return_value = {
            "code": 200,
            "data": {"timings": {"Fajr": "05:00"}},
        }

        with self.assertRaises(PrayerTimesAPIError):
            self.client.get_timings(41.0, 29.0)

    def test_wraps_request_failures(self) -> None:
        self.session.get.side_effect = requests.Timeout

        with self.assertRaises(PrayerTimesAPIError):
            self.client.get_timings(41.0, 29.0)


if __name__ == "__main__":
    unittest.main()
