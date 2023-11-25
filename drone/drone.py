import os
import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

app = Flask(__name__)  # Создание экземпляра Flask
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key')  # Секретный ключ
jwt = JWTManager(app)

logging.basicConfig(level=logging.INFO)

CONTENT_HEADER = {"Content-Type": "application/json"}

# Захардкодированные учетные данные для примера
USER_DATA = {
    "username": "admin",
    "password": "password123"
}


@app.route('/login', methods=['POST'])
def login():
    credentials = request.json
    username = credentials.get('username')
    password = credentials.get('password')

    if username == USER_DATA['username'] and password == USER_DATA['password']:
        access_token = create_access_token(identity={'name': username})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Wrong username or password"}), 401


@app.route("/set_command", methods=['POST'])
@jwt_required()
def set_command():
    content = request.json

    # Базовая валидация входящих данных
    if 'command' not in content or 'name' not in content:
        return jsonify({"msg": "Missing command or name"}), 400

    # Здесь должна быть логика обработки команд для дрона
    # ...

    return jsonify({"status": True})


if __name__ == "__main__":
    app.run(port=os.environ.get('DRONE_PORT', 6066), host="0.0.0.0")

