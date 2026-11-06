from datetime import date
from math import isfinite
from typing import Any, Mapping, Protocol

import requests


class PrayerTimesAPIError(Exception):
    """Raised when the prayer-times service cannot return valid timings."""


class PrayerTimesResponse(Protocol):
    def raise_for_status(self) -> None: ...

    def json(self) -> Any: ...


class PrayerTimesHTTPSession(Protocol):
    def get(
        self,
        url: str,
        *,
        params: Mapping[str, float | int],
        timeout: tuple[float, float],
    ) -> PrayerTimesResponse: ...


class PrayerTimesProvider(Protocol):
    def get_timings(self, latitude: float, longitude: float) -> Mapping[str, str]:
        """Return the day's prayer timings for the given coordinates."""


class AladhanPrayerTimesClient:
    BASE_URL = "https://api.aladhan.com/v1"
    CALCULATION_METHOD = 2
    REQUEST_TIMEOUT = (3.05, 15)
    REQUIRED_TIMINGS = ("Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha")

    def __init__(self, session: PrayerTimesHTTPSession | None = None) -> None:
        self._session = session if session is not None else requests

    def get_timings(self, latitude: float, longitude: float) -> Mapping[str, str]:
        if (
            not isfinite(latitude)
            or not isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise PrayerTimesAPIError("Geçerli bir enlem ve boylam gereklidir.")

        today = date.today().strftime("%d-%m-%Y")
        try:
            response = self._session.get(
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
        if (
            not isinstance(timings, dict)
            or not all(
                isinstance(timings.get(name), str) and timings[name].strip()
                for name in self.REQUIRED_TIMINGS
            )
        ):
            raise PrayerTimesAPIError("Aladhan API yanıtında namaz vakitleri bulunamadı.")

        return timings
