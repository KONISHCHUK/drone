import json
import random
import time
import logging
import requests
from requests.exceptions import RequestException
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

# Настройки логирования
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)  # создание экземпляра Flask

# Конфигурация JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # измените на ваш секретный ключ
jwt = JWTManager(app)

CONTENT_HEADER = {"Content-Type": "application/json"}
FPS_ENDPOINT_URI = "https://fps:6065/atm_input"
drones = []
area = []

class Drone:
    def __init__(self, coordinate, name, port, index):
        self.coordinate = coordinate
        self.name = name
        self.endpoint = "https://drone" + str(index) + ":" + str(port) + "/set_command"
        self.emergency = "https://drone" + str(index) + ":" + str(port) + "/emergency"
        self.token = ''
        self.drone_status = "Stopped"

@app.route('/login', methods=['POST'])
def login():
    # Ваш код для проверки учетных данных пользователя
    access_token = create_access_token(identity={'name': 'user_name'})
    return jsonify(access_token=access_token)

@app.route("/watchdog", methods=['POST'])
@jwt_required()
def watchdog():
    content = request.json
    return jsonify({"time": time.time()})

@app.route("/data_in", methods=['POST'])
@jwt_required()
def data_in():
    content = request.json
    global drones, area
    try:
        drone = next((d for d in drones if d.name == content['name']), None)
        if drone is None:
            return "Drone not found", 404

        drone.coordinate = content['coordinate']
        logging.info(f"[ATM_DATA_IN] {content['name']} located in: {content['coordinate']}")

        # Проверка выхода дрона за пределы рабочей зоны
        x, y = content['coordinate'][0], content['coordinate'][1]
        if len(area) > 0 and (x < area[0] or x > area[2] or y < area[1] or y > area[3]):
            logging.warning(f"{content['name']} is outside of area!")
            data = {"name": drone.name, "token": drone.token}
            requests.post(drone.emergency, data=json.dumps(data), headers=CONTENT_HEADER)

    except RequestException as e:
        logging.error(e)
        return "Error in processing request", 500
    return jsonify({"operation": "data_in", "status": True})

@app.route("/set_area", methods=['POST'])
@jwt_required()
def set_area():
    content = request.json
    global area
    try:
        area = content['area']
        logging.info(f"Area coordinates set: from ({area[0]};{area[1]}) to ({area[2]};{area[3]})")
    except Exception as e:
        logging.error(e)
        return "Error in processing request", 500
    return jsonify({"operation": "set_area", "status": True})

@app.route("/sign_up", methods=['POST'])
@jwt_required()
def sign_up():
    content = request.json
    global drones
    try:
        drone = Drone(content['coordinate'], content['name'], content['port'], content['index'])
        drones.append(drone)

        drone.token = random.randint(1000, 9999)
        data = {"name": content['name'], "command": "set_token", "token": drone.token}
        requests.post(drone.endpoint, data=json.dumps(data), headers=CONTENT_HEADER)

        logging.info(f"Drone signed up: {content['name']} in point {content['coordinate']} at port {content['port']}")
    except RequestException as e:
        logging.error(e)
        return "Error in processing request", 500
    return jsonify({"operation": "sign_up", "status": True})

@app.route("/sign_out", methods=['POST'])
@jwt_required()
def sign_out():
    content = request.json
    global drones
    try:
        drone = next((d for d in drones if d.name == content['name']), None)
        if drone is None:
            return "Drone not found", 404

        drones.remove(drone)
        logging.info(f"Deleted drone: {content['name']}")
    except Exception as e:
        logging.error(e)
        return "Error in processing request", 500
    return jsonify({"operation": "sign_out", "status": True})

@app.route("/new_task", methods=['POST'])
@jwt_required()
def new_task():
    content = request.json
    global drones
    try:
        drone = next((d for d in drones if d.name == content['name']), None)
        if drone is None:
            return "Drone not found", 404

        if drone.drone_status != "Active":
            drone.drone_status = "Active"
            data = {"name": content['name'], "command": "task_status_change", "task_status": "Accepted", "token": drone.token, "hash": len(content['points'])}
            requests.post(drone.endpoint, data=json.dumps(data), headers=CONTENT_HEADER)

            time.sleep(2)  # Ожидание перед отправкой следующего запроса

            data = {"name": content['name'], "points": content['points'], "task_status": "Accepted"}
            requests.post(FPS_ENDPOINT_URI, data=json.dumps(data), headers=CONTENT_HEADER)
        else:
            data = {"name": content['name'], "token": drone.token}
            requests.post(drone.emergency, data=json.dumps(data), headers=CONTENT_HEADER)

    except RequestException as e:
        logging.error(e)
        return "Error in processing request", 400
    return jsonify({"operation": "new_task", "status": True})

if __name__ == "__main__":
    app.run(port=6064, host="0.0.0.0")
