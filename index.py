from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Конфигурация
TELEGRAM_TOKEN = "7713986785:AAGmmLHzw-deWhWP4WZBEDWfzQpDyl4sBr8"
STORMGLASS_API_KEY = "3e99f8b6-dcc3-11ef-acf2-0242ac130003-3e99f9d8-dcc3-11ef-acf2-0242ac130003"
CHAT_ID = -123456789  # Замените на ID вашей группы

@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Отправляет прогноз в заданное время."""
    try:
        # Рассчитываем текущее время по UTC+7 (вьетнамское время)
        current_hour = (datetime.utcnow().hour + 7) % 24

        # Утренний прогноз в 8:00
        if current_hour == 8:
            forecast = get_wave_forecast()
            text = f"🌅 *Good Morning Vietnam и ребята из команды Without Woman!*\n\n{forecast}"
            send_message(CHAT_ID, text, parse_mode="Markdown")
        # Прогноз в 12:00 и 15:00
        elif current_hour in [12, 15]:
            forecast = get_wave_forecast()
            text = f"🕛 *Актуальный прогноз:*\n\n{forecast}"
            send_message(CHAT_ID, text, parse_mode="Markdown")
        else:
            return jsonify({"message": "No forecast sent at this time"}), 200

        return jsonify({"message": "Forecast sent successfully!"}), 200
    except Exception as e:
        print(f"Ошибка при отправке прогноза: {e}")
        return jsonify({"error": "Failed to send forecast"}), 500

@app.route('/')
def index():
    """Проверка работы сервера."""
    return "Server is running", 200

def get_wave_forecast():
    """Получает прогноз волн с Stormglass API."""
    try:
        api_url = "https://api.stormglass.io/v2/weather/point"
        params = {
            "lat": 16.0502,
            "lng": 108.2498,
            "params": "waveHeight,windSpeed,windDirection,wavePeriod,waterTemperature,airTemperature",
            "source": "sg"
        }
        headers = {
            "Authorization": STORMGLASS_API_KEY
        }
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "hours" not in data or not data["hours"]:
            return "❌ Не удалось получить прогноз. Данные недоступны."

        nearest = data["hours"][0]
        wave_height = nearest.get("waveHeight", {}).get("sg", "нет данных")
        wave_period = nearest.get("wavePeriod", {}).get("sg", "нет данных")
        wind_speed = nearest.get("windSpeed", {}).get("sg", "нет данных")
        wind_direction = nearest.get("windDirection", {}).get("sg", "нет данных")
        water_temp = nearest.get("waterTemperature", {}).get("sg", "нет данных")
        air_temp = nearest.get("airTemperature", {}).get("sg", "нет данных")

        forecast = (
            f"🌊 *Прогноз волн для My Khe:*\n\n"
            f"🏄 Высота волн: *{wave_height} м*\n"
            f"📏 Интервал между волнами: *{wave_period} сек*\n"
            f"🍃 Скорость ветра: *{wind_speed} м/с*\n"
            f"🧭 Направление ветра: *{wind_direction}°*\n"
            f"🌡 Температура воды: *{water_temp}°C*\n"
            f"🌤 Температура воздуха: *{air_temp}°C*\n\n"
            f"Источник данных: [Stormglass.io](https://stormglass.io)"
        )
        return forecast
    except Exception as e:
        print(f"Ошибка при получении прогноза: {e}")
        return "❌ Не удалось получить прогноз. Попробуйте позже."

def send_message(chat_id, text, parse_mode=None):
    """Отправляет текстовое сообщение в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

# Указываем обработчик для Vercel
handler = app
