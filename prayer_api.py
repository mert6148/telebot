from datetime import date
from typing import Mapping, Protocol

import requests


class PrayerTimesAPIError(Exception):
    """Raised when the prayer-times service cannot return valid timings."""


class PrayerTimesProvider(Protocol):
    def get_timings(self, latitude: float, longitude: float) -> Mapping[str, str]:
        """Return the day's prayer timings for the given coordinates."""


class AladhanPrayerTimesClient:
    BASE_URL = "https://api.aladhan.com/v1"
    CALCULATION_METHOD = 2
    REQUEST_TIMEOUT = (3.05, 15)

    def get_timings(self, latitude: float, longitude: float) -> Mapping[str, str]:
        today = date.today().strftime("%d-%m-%Y")
        try:
            response = requests.get(
                f"{self.BASE_URL}/timings/{today}",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "method": self.CALCULATION_METHOD,
                },
                timeout=self.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PrayerTimesAPIError("Aladhan API isteği başarısız oldu.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise PrayerTimesAPIError("Aladhan API geçerli JSON döndürmedi.") from exc

        if not isinstance(payload, dict) or payload.get("code") != 200:
            raise PrayerTimesAPIError("Aladhan API başarılı bir yanıt döndürmedi.")

        data = payload.get("data")
        timings = data.get("timings") if isinstance(data, dict) else None
        if not isinstance(timings, dict) or not timings or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in timings.items()
        ):
            raise PrayerTimesAPIError("Aladhan API yanıtında namaz vakitleri bulunamadı.")

        return timings
