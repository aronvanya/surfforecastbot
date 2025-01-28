from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Корневой маршрут для проверки."""
    return "Server is running!", 200

@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Маршрут для отправки прогноза."""
    return jsonify({"message": "Forecast route is working!"}), 200

# Указываем обработчик для Vercel
handler = app
