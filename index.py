def get_wave_forecast():
    """Получает прогноз волн с Stormglass API."""
    try:
        api_url = "https://api.stormglass.io/v2/weather/point"
        params = {
            "lat": 16.0502,  # Координаты пляжа My Khe
            "lng": 108.2498,
            "params": "waveHeight,windSpeed,windDirection,wavePeriod",  # Исправленный параметр
            "source": "sg"  # Используем источник Stormglass
        }
        headers = {
            "Authorization": STORMGLASS_API_KEY
        }

        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()  # Вызывает ошибку, если ответ не 2xx
        data = response.json()

        # Проверяем, есть ли данные
        if "hours" not in data or not data["hours"]:
            return "❌ Не удалось получить прогноз. Данные недоступны."

        # Получаем ближайший прогноз
        nearest = data["hours"][0]
        wave_height = nearest.get("waveHeight", {}).get("sg", "нет данных")
        wind_speed = nearest.get("windSpeed", {}).get("sg", "нет данных")
        wind_direction = nearest.get("windDirection", {}).get("sg", "нет данных")
        wave_period = nearest.get("wavePeriod", {}).get("sg", "нет данных")

        forecast = (
            f"🌊 *Прогноз волн для My Khe:*\n\n"
            f"🏄 Высота волн: *{wave_height} м*\n"
            f"📏 Интервал между волнами: *{wave_period} сек*\n"
            f"🍃 Скорость ветра: *{wind_speed} м/с*\n"
            f"🧭 Направление ветра: *{wind_direction}°*\n\n"
            f"Источник данных: [Stormglass.io](https://stormglass.io)"
        )
        return forecast

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка при получении прогноза: {e}")
        return "❌ Не удалось получить прогноз. Попробуйте позже."
