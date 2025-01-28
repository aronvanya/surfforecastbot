from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    """Проверка работы сервера."""
    return "Server is running!", 200

@app.route('/send_forecast', methods=['POST'])
def send_forecast():
    """Пример обработчика для теста."""
    return jsonify({"message": "Forecast route is working!"}), 200

# Указываем обработчик для Vercel
handler = app
