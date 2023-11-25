#!/usr/bin/env python

import hashlib
import os
from random import randrange
from flask import Flask, request, jsonify
import implementation

CONTENT_HEADER = {"Content-Type": "application/json"}
ATM_ENDPOINT_URI = "http://atm:6064/data_in"
ATM_SIGN_UP_URI = "http://atm:6064/sign_up"
ATM_SIGN_OUT_URI = "http://atm:6064/sign_out"
FPS_ENDPOINT_URI = "http://fps:6065/data_in"
DELIVERY_INTERVAL_SEC = 1
drones = []

host_name = "0.0.0.0"
port = os.environ['DRONE_PORT'] #6066
app = Flask(__name__)             # create an app instance




@app.route("/set_command", methods=['POST'])
def set_command():
    global drones
    try:
        content = request.json
        # print(f'[DRONE_DEBUG] received {content}')
        if content['command'] == 'initiate':
            print(port)
            tmp = implementation.Drone(content['coordinate'], content['name'], content['psswd'])
            drones.append(tmp)
            print (f"Added in point {tmp.coordinate}")
        else:
            
            drone = list(filter(lambda i: content['name'] == i.name, drones))
            
            if len(drone) > 1:
                print(f'[DRONE_SET_COMMAND_ERROR]')
                print(f'Nonunique name: {content["name"]}')
                return "BAD ITEM NAME", 400
            
            drone = drone[0] 
            if content['command'] == 'set_token':
                    drone.token = content['token']
                    print(f'[DRONE_TOKEN_SET]')
            elif content['command'] == 'task_status_change':
                    if drone.token == content['token']:
                        drone.task_status = content['task_status']
                        drone.hash = content['hash']
                        print(f'[DRONE_TASK_ACCEPTED]')
            elif drone.psswd == content['psswd']:
                if content['command'] == 'start':
                    drone.start(content["speed"])
                if content['command'] == 'stop':
                    drone.stop()
                if content['command'] == 'sign_out':
                    drone.sign_out()
                    drones.remove(drone)
                if content['command'] == 'clear_flag':
                    drone.clear_emergency_flag()
                if content['command'] == 'set_task':
                    if drone.hash == len(content["points"]):
                        print(f'[DRONE_SET_TASK]')
                        print(f'Point added!')
                        drone.task_points = content["points"]
                if content['command'] == 'register':
                    drone.register()
                
    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})

@app.route("/emergency", methods=['POST'])
def emergency():
    global drones
    try:
        content = request.json
        drone = list(filter(lambda i: content['name'] == i.name, drones))
        if len(drone) > 1:
            print(f'[DRONE_EMERGENCY_ERROR]')
            print(f'Nonunique name: {content["name"]}')
            return "BAD ITEM NAME", 400
        else:
            if content['token'] == drone[0].token:
                drone[0].status = "Blocked"
                drone[0].emergency() 
                print(f"[ATTENTION]")
                print(f"{content['name']} emergency stopped!")

    except Exception as e:
        print(f'exception raised: {e}')
        return "MALFORMED REQUEST", 400
    return jsonify({"status": True})




if __name__ == "__main__":
    # threading.Thread(
    #             target=lambda: temperature_pushing()).start()
    app.run(port = port, host=host_name)
    
   