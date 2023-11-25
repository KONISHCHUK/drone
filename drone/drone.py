#!/usr/bin/env python

import os
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from werkzeug.security import check_password_hash

import implementation
import logging

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key')  # Секретный ключ для JWT
jwt = JWTManager(app)

logging.basicConfig(level=logging.INFO)

CONTENT_HEADER = {"Content-Type": "application/json"}
ATM_ENDPOINT_URI = "https://atm:6064/data_in"
ATM_SIGN_UP_URI = "https://atm:6064/sign_up"
ATM_SIGN_OUT_URI = "https://atm:6064/sign_out"
FPS_ENDPOINT_URI = "https://fps:6065/data_in"
DELIVERY_INTERVAL_SEC = 1
drones = {}


host_name = "0.0.0.0"
port = os.environ.get('DRONE_PORT', 6066)  # Значение по умолчанию 6066

# Пример базы данных пользователей
users = {
    "admin": {
        "password": "hashed_password_here"  # В реальном приложении пароли должны быть хешированы
    }
    # Добавьте других пользователей по необходимости
}


@app.route("/login", methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = users.get(username, None)
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

@app.route("/set_command", methods=['POST'])
@jwt_required()  # Требует наличия валидного JWT токена
def set_command():
    try:
        content = request.json
        drone_name = content.get('name')
        command = content.get('command')
        drone = drones.get(drone_name)

        if not drone:
            return jsonify({"msg": "Drone not found"}), 404

        # Проверка необходимых ключей в JSON
        if not all(key in content for key in ['command', 'name']):
            return jsonify({"msg": "Missing required data"}), 400

        if command == 'set_token':
            drone.token = content['token']
            logging.info(f'[DRONE_TOKEN_SET]')
        elif command == 'task_status_change' and drone.token == content['token']:
            drone.task_status = content['task_status']
            drone.hash = content['hash']
            logging.info(f'[DRONE_TASK_ACCEPTED]')
        elif drone.psswd == content['psswd']:
            if command == 'start':
                drone.start(content["speed"])
            elif command == 'stop':
                drone.stop()
            elif command == 'sign_out':
                drone.sign_out()
                drones.pop(drone_name)
            elif command == 'clear_flag':
                drone.clear_emergency_flag()
            elif command == 'set_task' and drone.hash == len(content["points"]):
                drone.task_points = content["points"]
                logging.info(f'[DRONE_SET_TASK] Point added!')
            elif command == 'register':
                drone.register()
            else:
                return jsonify({"msg": "Unknown or unauthorized command"}), 400

    except Exception as e:
        logging.error(f'exception raised: {e}')
        return jsonify({"msg": "Internal Server Error"}), 500

    return jsonify({"status": True})

@app.route("/emergency", methods=['POST'])
@jwt_required()
def emergency():
    try:
        content = request.json
        drone_name = content.get('name')
        drone = drones.get(drone_name)

        if not drone:
            return jsonify({"msg": "Drone not found"}), 404

        # Обработка аварийной ситуации
        ...

    except Exception as e:
        logging.error(f'exception raised: {e}')
        return jsonify({"msg": "Internal Server Error"}), 500

    return jsonify({"status": True})

if __name__ == "__main__":
    app.run(port=os.environ.get('DRONE_PORT', 6066), ssl_context=('storage/cert.pem', 'storage/key.pem'))  # Запуск с поддержкой HTTPS
