from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# 🔑 Конфигурация
TELEGRAM_TOKEN = "7713986785:AAGbL5WZBEDWfzQpDyl4sBr8"
STORMGLASS_API_KEY = "3e99f8b6-dcc3-11ef-acf2-0242ac130003-3e99f9d8-dcc3-11ef-acf2-0242ac130003"

# 📌 Хранилище активных групп (загружаем из переменной окружения)
active_groups = set(map(int, os.getenv("ACTIVE_GROUPS", "").split(","))) if os.getenv("ACTIVE_GROUPS") else set()

def save_active_groups():
    """Сохраняет список активных групп в переменную окружения."""
    os.environ["ACTIVE_GROUPS"] = ",".join(map(str, active_groups))
    print(f"💾 [LOG] Группы сохранены: {active_groups}")

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
            if chat_id not in active_groups:
                active_groups.add(chat_id)
                save_active_groups()  # Сохраняем изменения
                print(f"✅ [LOG] Добавлена новая группа: {chat_id}")

        # Обработка команды /start
        if "text" in message and message["text"] == "/start":
            send_message(chat_id, "👋 Бот готов к работе в этой группе!", parse_mode="Markdown")
            return jsonify({"status": "ok"}), 200

    return jsonify({"status": "ignored"}), 200


@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Отправляет прогноз в группы."""
    try:
        print(f"📡 [LOG] Запрос на прогноз получен. Активные группы: {active_groups}")

        if not active_groups:
            print("❌ [LOG] Нет активных групп для отправки прогноза.")
            return jsonify({"message": "No active groups to send forecast"}), 200

        # Получаем текущее UTC-время и переводим во вьетнамское
        current_time = datetime.utcnow()
        viet_hour = (current_time.hour + 7) % 24
        viet_minute = current_time.minute

        print(f"⏳ [LOG] Время сейчас во Вьетнаме: {viet_hour}:{viet_minute}")

        # Запланированные времена отправки с допуском ±5 минут
        forecast_times = [(10, m) for m in range(0, 6)] + \
                         [(12, m) for m in range(0, 6)] + \
                         [(15, m) for m in range(0, 6)]

        if (viet_hour, viet_minute) not in forecast_times:
            print(f"🚫 [LOG] Сейчас {viet_hour}:{viet_minute}, прогноз не отправляется.")
            return jsonify({"message": "No forecast sent at this time"}), 200

        print(f"✅ [LOG] Отправка прогноза в {viet_hour}:{viet_minute}!")

        for group_id in active_groups:
            forecast = get_wave_forecast()
            if viet_hour == 10:
                text = f"🌅 *Good Morning Vietnam!*\n\n{forecast}"
            elif viet_hour == 12:
                text = f"🕛 *Актуальный прогноз:*\n\n{forecast}"
            elif viet_hour == 15:
                text = f"🕒 *Обновленный прогноз:*\n\n{forecast}"

            send_message(group_id, text, parse_mode="Markdown")

        return jsonify({"message": "Forecast sent successfully!"}), 200

    except Exception as e:
        print(f"❌ [LOG] Ошибка при отправке прогноза: {e}")
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
