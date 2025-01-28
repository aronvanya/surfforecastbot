from flask import Flask, request, jsonify
import os
import requests
import threading
import schedule
import time

app = Flask(__name__)

# Переменные окружения
TELEGRAM_TOKEN = "7713986785:AAGmmLHzw-deWhWP4WZBEDWfzQpDyl4sBr8"
STORMGLASS_API_KEY = "3e99f8b6-dcc3-11ef-acf2-0242ac130003-3e99f9d8-dcc3-11ef-acf2-0242ac130003"
CHAT_ID = -123456789  # Замените на ID вашей группы

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука Telegram."""
    try:
        data = request.get_json()
        if data and "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text == "/start":
                send_message(chat_id, (
                    "👋 Привет! Я бот для прогноза волн. 🌊\n\n"
                    "Я автоматически отправляю прогноз в 8:00, 12:00 и 15:00 по вьетнамскому времени.\n\n"
                    "Вы также можете использовать команду /forecast, чтобы получить текущий прогноз."
                ))
                return jsonify({"message": "Start command processed"}), 200

            if text == "/forecast":
                forecast = get_wave_forecast()
                send_message(chat_id, forecast, parse_mode="Markdown")
                return jsonify({"message": "Forecast command processed"}), 200

            send_message(chat_id, "❌ Неизвестная команда. Попробуйте /start или /forecast.")
            return jsonify({"message": "Unknown command processed"}), 200

        return jsonify({"message": "Webhook received!"}), 200
    except Exception as e:
        print(f"Ошибка в обработке вебхука: {e}")
        return jsonify({"error": "Internal server error"}), 500

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

def schedule_jobs():
    """Планировщик задач."""
    schedule.every().day.at("08:00").do(lambda: send_morning_forecast())
    schedule.every().day.at("12:00").do(lambda: send_afternoon_forecast())
    schedule.every().day.at("15:00").do(lambda: send_afternoon_forecast())

    while True:
        schedule.run_pending()
        time.sleep(1)

def send_morning_forecast():
    """Утренний прогноз с приветствием."""
    forecast = get_wave_forecast()
    text = f"🌅 *Good Morning Vietnam и ребята из команды Without Woman!*\n\n{forecast}"
    send_message(CHAT_ID, text, parse_mode="Markdown")

def send_afternoon_forecast():
    """Дневной прогноз."""
    forecast = get_wave_forecast()
    text = f"🕛 *Актуальный прогноз:*\n\n{forecast}"
    send_message(CHAT_ID, text, parse_mode="Markdown")

# Запуск планировщика в отдельном потоке
thread = threading.Thread(target=schedule_jobs)
thread.daemon = True
thread.start()

# Указываем handler для Vercel
handler = app
