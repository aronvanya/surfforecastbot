from flask import Flask, request, jsonify
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
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
    """Получает прогноз волн с Surfline."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }
        response = requests.get(SURFLINE_URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Парсим данные о волнах
        wave_height = soup.find("span", class_="quiver-surf-height").get_text(strip=True)
        wave_condition = soup.find("span", class_="quiver-spot-conditions-summary__text").get_text(strip=True)

        return f"🌊 *Прогноз волн для My Khe:*\n\n🏄 Высота волн: *{wave_height}*\n🌤 Условия: *{wave_condition}*\n\nПодробнее: [Surfline]({SURFLINE_URL})"

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении прогноза: {e}")
        return "❌ Не удалось получить прогноз. Surfline блокирует запрос."
    except AttributeError:
        print("Ошибка: структура сайта Surfline изменилась.")
        return "❌ Не удалось найти данные на странице Surfline. Возможно, структура сайта изменилась."
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return "❌ Произошла ошибка при обработке данных. Попробуйте позже."

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
