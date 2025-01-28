from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Server is running!", 200

@app.route('/test', methods=['POST'])
def test():
    return jsonify({"message": "Test route is working!"}), 200

# Экспортируем обработчик для Vercel
app = app
