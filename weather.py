import os
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv()


WEATHER_LAT = os.getenv("WEATHER_LAT")
WEATHER_LON = os.getenv("WEATHER_LON")
WEATHER_CITY = os.getenv("WEATHER_CITY")

if not WEATHER_LAT or not WEATHER_LON:
    raise RuntimeError(
        "Missing WEATHER_LAT or WEATHER_LON in .env. "
        "Find your coordinates on Google Maps (right-click your location) "
        "and add them to your .env file."
    )

FORECAST_HOURS = list(range(9, 22, 2))
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Foggy",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with hail",
}


RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}
SNOW_CODES = {71, 73, 75, 77, 85, 86}
FREEZING_CODES = {56, 57, 66, 67}
THUNDER_CODES = {95, 96, 99}

def _describe(code):
    return WEATHER_CODES.get(code, "Unknown conditions")

def _format_hour(hour_24):
    """12 -> '12 PM', 9 -> '9 AM', 21 -> '9 PM'."""
    if hour_24 == 0:
        return "12 AM"
    if hour_24 < 12:
        return f"{hour_24} AM"
    if hour_24 == 12:
        return "12 PM"
    return f"{hour_24 - 12} PM"

def _build_alerts(daytime_codes, low_temp, high_temp):
    """
    Look at the day's weather codes and return a list of alert strings.
    Empty list means no alerts.
    """
    alerts = []
    code_set = set(daytime_codes)

    if code_set & FREEZING_CODES:
        alerts.append("⚠️ Freezing rain expected — drive carefully and watch for ice.")
    elif code_set & THUNDER_CODES:
        alerts.append("⛈️ Thunderstorms expected — stay indoors when possible.")
    elif code_set & RAIN_CODES:
        alerts.append("☔ Rain expected — bring an umbrella!")

    if code_set & SNOW_CODES:
        alerts.append("❄️ Snow expected — bundle up and allow extra travel time.")

    if low_temp <= 32:
        alerts.append(f"🥶 It's freezing out (low of {low_temp}°F) — wear a heavy coat.")
    elif low_temp <= 45 and not (code_set & SNOW_CODES):
        alerts.append(f"🧥 It'll be chilly (low of {low_temp}°F) — grab a jacket.")

    if high_temp >= 90:
        alerts.append(f"🥵 It'll be hot (high of {high_temp}°F) — stay hydrated.")

    return alerts

def get_weather_message():
    """
    Fetches today's weather and returns a formatted multi-line string
    ready to drop into a text message, email, or chat post.
    """
    params = {
        "latitude": WEATHER_LAT,
        "longitude": WEATHER_LON,
        "hourly": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
        "forecast_days": 1,
    }
    data = requests.get(
        "https://api.open-meteo.com/v1/forecast", params=params, timeout=10
    ).json()

    daily = data["daily"]
    high = round(daily["temperature_2m_max"][0])
    low = round(daily["temperature_2m_min"][0])
    summary = _describe(daily["weather_code"][0])

    hourly_lookup = {}
    daytime_codes = []
    for iso_time, temp, code in zip(
        data["hourly"]["time"],
        data["hourly"]["temperature_2m"],
        data["hourly"]["weather_code"],
    ):
        dt = datetime.fromisoformat(iso_time)
        hourly_lookup[dt.hour] = (round(temp), code)
        if 7 <= dt.hour <= 22:
            daytime_codes.append(code)

    location_label = WEATHER_CITY or f"{WEATHER_LAT}, {WEATHER_LON}"

    lines = []
    lines.append(f"🌤️ Weather for {location_label}")
    lines.append(f"{summary} — high {high}°F, low {low}°F")

    alerts = _build_alerts(daytime_codes, low, high)
    if alerts:
        lines.append("")
        lines.extend(alerts)

    lines.append("")
    lines.append("Hourly forecast:")
    for hour_24 in FORECAST_HOURS:
        if hour_24 not in hourly_lookup:
            continue
        temp, code = hourly_lookup[hour_24]
        lines.append(f"  {_format_hour(hour_24)}: {temp}°F, {_describe(code)}")

    return "\n".join(lines)
