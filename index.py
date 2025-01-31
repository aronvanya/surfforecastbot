from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# 🔑 Конфигурация
TELEGRAM_TOKEN = "7713986785:AAGmmLHzw-deWhWP4WZBEDWfzQpDyl4sBr8"
STORMGLASS_API_KEY = "3e99f8b6-dcc3-11ef-acf2-0242ac130003-3e99f9d8-dcc3-11ef-acf2-0242ac130003"

# 📌 Хранилище активных групп (в памяти)
active_groups = set()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обрабатывает сообщения из Telegram."""
    data = request.get_json()
    print(f"📩 [LOG] Получены данные: {data}")

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]

        # Если это группа, добавляем её в список активных
        if chat_type in ["group", "supergroup"]:
            active_groups.add(chat_id)
            print(f"✅ [LOG] Группа {chat_id} добавлена в список активных")

        if "text" in message and message["text"] == "/start":
            send_message(chat_id, "👋 Бот готов к работе в этой группе!", parse_mode="Markdown")

    return jsonify({"status": "ok"}), 200

@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Отправляет прогноз в группы."""
    try:
        # Обновляем список групп перед отправкой
        update_active_groups()

        if not active_groups:
            print("❌ [LOG] Нет активных групп для отправки прогноза.")
            return jsonify({"message": "No active groups"}), 200

        # Текущее вьетнамское время (UTC+7)
        current_hour = (datetime.utcnow().hour + 7) % 24
        current_minute = datetime.utcnow().minute

        # ✅ Промежуток 5 минут (например, 8:00–8:05)
        if (8, 0) <= (current_hour, current_minute) <= (9, 5):
            prefix = "🌅 *Good Morning Vietnam!*\n\n"
        elif (12, 0) <= (current_hour, current_minute) <= (12, 5):
            prefix = "🕛 *Актуальный прогноз:*\n\n"
        elif (15, 0) <= (current_hour, current_minute) <= (15, 5):
            prefix = "🕒 *Обновленный прогноз:*\n\n"
        else:
            print(f"⏳ [LOG] Сейчас {current_hour}:{current_minute}, прогноз не отправляется.")
            return jsonify({"message": "Not forecast time"}), 200

        # Запрашиваем прогноз
        forecast = get_wave_forecast()

        for group_id in active_groups:
            send_message(group_id, f"{prefix}{forecast}", parse_mode="Markdown")

        return jsonify({"message": "Forecast sent"}), 200

    except Exception as e:
        print(f"❌ [LOG] Ошибка при отправке прогноза: {e}")
        return jsonify({"error": "Failed to send forecast"}), 500

@app.route('/update_groups', methods=['POST'])
def update_groups():
    """Обновляет список активных групп."""
    update_active_groups()
    return jsonify({"message": "Groups updated"}), 200

def update_active_groups():
    """Запрашивает список чатов, где бот является участником."""
    global active_groups
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        new_groups = set()
        for update in data.get("result", []):
            if "message" in update:
                chat = update["message"]["chat"]
                if chat["type"] in ["group", "supergroup"]:
                    new_groups.add(chat["id"])

        active_groups.update(new_groups)
        print(f"📡 [LOG] Обновленный список групп: {active_groups}")

    except Exception as e:
        print(f"❌ [LOG] Ошибка при обновлении списка групп: {e}")

def get_wave_forecast():
    """Получает прогноз волн с Stormglass API."""
    try:
        api_url = "https://api.stormglass.io/v2/weather/point"
        params = {
            "lat": 16.0502,
            "lng": 108.2498,
            "params": "waveHeight,wavePeriod,swellHeight,swellPeriod,windSpeed,waterTemperature",
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
        wind_speed = nearest.get("windSpeed", {}).get("sg", "❌ Нет данных")
        water_temp = nearest.get("waterTemperature", {}).get("sg", "❌ Нет данных")

        forecast = (
            f"🌊 *Прогноз волн для My Khe:*\n"
            f"🏄 Высота волн: *{wave_height} м*\n"
            f"📏 Интервал между волнами: *{wave_period} сек*\n"
            f"🌊 Высота свелла: *{swell_height} м*\n"
            f"⏳ Интервал между свеллами: *{swell_period} сек*\n"
            f"🍃 Скорость ветра: *{wind_speed} м/с*\n"
            f"🌡 Температура воды: *{water_temp}°C*\n"
            f"---------------------------\n"
            f"Источник данных: [Stormglass.io](https://stormglass.io)"
        )
        return forecast
    except Exception as e:
        print(f"❌ [LOG] Ошибка при получении прогноза: {e}")
        return "❌ Не удалось получить прогноз. Попробуйте позже."

def send_message(chat_id, text, parse_mode=None):
    """Отправляет сообщение в Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"📨 [LOG] Сообщение отправлено в {chat_id}: {text}")
    except Exception as e:
        print(f"❌ [LOG] Ошибка при отправке сообщения: {e}")

# Указываем обработчик для Vercel
app = app
