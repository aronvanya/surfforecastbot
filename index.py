from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Корневой маршрут для проверки."""
    return "Server is running!", 200

@app.route('/test', methods=['POST'])
def test():
    """Тестовый маршрут для проверки POST-запросов."""
    return jsonify({"message": "Test route is working!"}), 200

# Указываем обработчик для Vercel
handler = app
