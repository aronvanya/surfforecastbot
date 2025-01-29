from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# Конфигурация
TELEGRAM_TOKEN = "7713986785:AAGmmLHzw-deWhWP4WZBEDWfzQpDyl4sBr8"
STORMGLASS_API_KEY = "3e99f8b6-dcc3-11ef-acf2-0242ac130003-3e99f9d8-dcc3-11ef-acf2-0242ac130003"

# Хранилище активных групп
active_groups = set()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обрабатывает сообщения из Telegram."""
    data = request.get_json()
    print(f"Получены данные: {data}")

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]

        if chat_type in ["group", "supergroup"]:
            if chat_id not in active_groups:
                active_groups.add(chat_id)
                print(f"Добавлена новая группа: {chat_id}")

        if "text" in message and message["text"] == "/start":
            send_message(chat_id, "👋 Бот готов к работе в этой группе!", parse_mode="Markdown")
            return jsonify({"status": "ok"}), 200

    return jsonify({"status": "ignored"}), 200

@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Отправляет прогноз в группы."""
    try:
        if not active_groups:
            print("Нет активных групп для отправки прогноза.")
            return jsonify({"message": "No active groups to send forecast"}), 200

        current_time = datetime.utcnow()  # Время в UTC
        current_hour = (current_time.hour + 7) % 24  # UTC+7 (вьетнамское время)
        current_minute = current_time.minute

        if (current_hour, current_minute) not in [(8, 0), (12, 0), (15, 36)]:
            print(f"Прогноз в {current_hour}:{current_minute} не отправляется.")
            return jsonify({"message": "No forecast sent at this time"}), 200

        for group_id in active_groups:
            forecast = get_wave_forecast()
            if current_hour == 8 and current_minute == 0:
                text = f"🌅 *Good Morning Vietnam!*\n\n{forecast}"
            elif current_hour == 12 and current_minute == 0:
                text = f"🕛 *Актуальный прогноз:*\n\n{forecast}"
            elif current_hour == 15 and current_minute == 36:
                text = f"🕒 *Обновленный прогноз:*\n\n{forecast}"
            send_message(group_id, text, parse_mode="Markdown")

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
            "params": "waveHeight,wavePeriod,swellHeight,swellPeriod,waveDirection,windSpeed,windDirection,waterTemperature",
            "source": "sg"
        }
        headers = {"Authorization": STORMGLASS_API_KEY}
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "hours" not in data or not data["hours"]:
            return "❌ Не удалось получить прогноз. Данные недоступны."

        nearest = data["hours"][0]
        wave_height = nearest.get("waveHeight", {}).get("sg", "❌ Нет данных")
        wave_period = nearest.get("wavePeriod", {}).get("sg", "❌ Нет данных")
        swell_height = nearest.get("swellHeight", {}).get("sg", "❌ Нет данных")
        swell_period = nearest.get("swellPeriod", {}).get("sg", "❌ Нет данных")
        wave_direction = nearest.get("waveDirection", {}).get("sg", "❌ Нет данных")
        wind_speed = nearest.get("windSpeed", {}).get("sg", "❌ Нет данных")
        wind_direction = nearest.get("windDirection", {}).get("sg", "❌ Нет данных")
        water_temp = nearest.get("waterTemperature", {}).get("sg", "❌ Нет данных")

        # Получаем данные о восходе и фазе луны
        sunrise, sunset, moon_phase = get_sun_moon_data()

        forecast = (
            f"🌊 *Прогноз волн для My Khe:*\n"
            f"🏄 Высота волн: *{wave_height} м*\n"
            f"📏 Интервал между волнами: *{wave_period} сек*\n"
            f"🌊 Высота свелла: *{swell_height} м*\n"
            f"⏳ Интервал между свеллами: *{swell_period} сек*\n"
            f"🧭 Направление волн: *{wave_direction}°*\n"
            f"🍃 Скорость ветра: *{wind_speed} м/с*\n"
            f"🧭 Направление ветра: *{wind_direction}°*\n"
            f"🌡 Температура воды: *{water_temp}°C*\n"
            f"🌅 Восход: *{sunrise}* | 🌇 Закат: *{sunset}*\n"
            f"🌙 Фаза Луны: *{moon_phase}*\n"
            f"---------------------------\n"
            f"Источник данных: [Stormglass.io](https://stormglass.io)"
        )
        return forecast
    except Exception as e:
        print(f"Ошибка при получении прогноза: {e}")
        return "❌ Не удалось получить прогноз. Попробуйте позже."

def get_sun_moon_data():
    """Получает данные о восходе, закате и фазе Луны."""
    try:
        api_url = "https://api.stormglass.io/v2/astronomy/point"
        params = {
            "lat": 16.0502,
            "lng": 108.2498
        }
        headers = {"Authorization": STORMGLASS_API_KEY}
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" not in data or not data["data"]:
            return "❌ Нет данных", "❌ Нет данных", "❌ Нет данных"

        sunrise = data["data"][0].get("sunrise", "❌ Нет данных")
        sunset = data["data"][0].get("sunset", "❌ Нет данных")
        moon_phase = data["data"][0].get("moonPhase", "❌ Нет данных")

        return sunrise, sunset, moon_phase
    except Exception as e:
        print(f"Ошибка при получении данных о солнце и луне: {e}")
        return "❌ Нет данных", "❌ Нет данных", "❌ Нет данных"

def send_message(chat_id, text, parse_mode=None):
    """Отправляет сообщение в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Сообщение отправлено в {chat_id}: {text}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

# Указываем обработчик для Vercel
app = app
