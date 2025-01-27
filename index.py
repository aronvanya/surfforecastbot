from flask import Flask, request, jsonify
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# Переменные окружения
TELEGRAM_TOKEN = "7713986785:AAGmmLHzw-deWhWP4WZBEDWfzQpDyl4sBr8"
SURFLINE_URL = "https://www.surfline.com/surf-report/my-khe/640a5eaa99dd4458250abcf8"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхука Telegram."""
    try:
        data = request.get_json()
        print(f"Получены данные: {data}")

        if data and "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text == "/start":
                send_message(chat_id, (
                    "👋 Привет! Я бот для прогноза волн. 🌊\n\n"
                    "Используйте команду /forecast, чтобы получить текущий прогноз для My Khe."
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
    """Получает прогноз волн через Selenium."""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.get(SURFLINE_URL)

        wave_height = driver.find_element_by_css_selector(".quiver-surf-height").text
        wave_period = driver.find_element_by_css_selector(".quiver-surf-period").text
        wind_speed = driver.find_element_by_css_selector(".quiver-wind-speed").text
        wind_direction = driver.find_element_by_css_selector(".quiver-wind-direction-text").text

        driver.quit()

        forecast = (
            f"🌊 *Прогноз волн для My Khe:*\n\n"
            f"🏄 Высота волн: *{wave_height}*\n"
            f"📏 Интервал между волнами: *{wave_period}*\n"
            f"🍃 Скорость ветра: *{wind_speed}*\n"
            f"🧭 Направление ветра: *{wind_direction}*\n\n"
            f"Подробнее: [Surfline]({SURFLINE_URL})"
        )
        return forecast

    except Exception as e:
        print(f"Ошибка при получении прогноза через Selenium: {e}")
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
        print(f"Сообщение отправлено: {text}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

if __name__ == '__main__':
    app.run(debug=True)
