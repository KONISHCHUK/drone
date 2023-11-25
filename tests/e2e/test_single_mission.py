from multiprocessing import Process, Queue
import random
from time import sleep
from flask import Flask, jsonify, request
import json
import requests



host_name = "0.0.0.0"
port = 6062

REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "auth": "very-secure-token"
}

FPS_COMMAND_ENDPOINT_URI = 'http://0.0.0.0:6065/set_command'
ATM_COMMAND_ENDPOINT_URI =  'http://0.0.0.0:6064/set_area'

global_events_log = Queue()


app = Flask(__name__)  # create an app instance


@app.route("/", methods=['POST'])
def data_receive():
    global global_events_log
    try:
        content = request.json
        #print(f"received message: {content['device']} {content['value']}")
        global_events_log.put(content)                
    except Exception as _:
        #print(e)
        return "BAD DATA RESPONSE", 400
    return jsonify({"status": True})


def initiate(name, coordinate, psswd):
    data = {
        "command" : "initiate",
        "name" : name, #"ITEM1",
        "coordinate" : coordinate, #[2,2,2],
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def register(name, psswd):
    data = {
        "command" : "register",
        "name" : name, #"ITEM1",
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def set_area(area):
    data = {
        "area" : area #[-1,-1,100,100]
    }
    response = requests.post(
        ATM_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def start(name, speed, psswd):
    data = {
        "command" : "start",
        "name" : name, # "ITEM1",
        "speed" : speed, #1,
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def stop(name, psswd):
    data = {
        "command" : "stop",
        "name" : name, #"ITEM1",
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def sign_out(name, psswd):
    data = {
        "command" : "sign_out",
        "name" : name, #"ITEM1",
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def move_to(name, coordinate, speed, psswd):
    data = {
        "command" : "move_to",
        "name" : name, #"ITEM1",
        "coordinate" : coordinate, #[3,5,1],
        "speed" : speed, #1,
        "psswd": psswd #12345
    } 
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def new_task(name, points, psswd):
    data = {
        "command" : "new_task",
        "name" : name, #"ITEM1",
        "points" : points,#, [[5,5,5,0],[8,8,8,1],[11,11,11,1],[16,16,11,0]],
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

def clear_flag(name, psswd):
    data = {
        "command" : "clear_flag",
        "name" : name, #"ITEM1",
        "psswd": psswd #12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200
    

###
### Functionally tests
###

def test_single_full_functionality():
    global global_events_log
    server = Process(target=lambda: app.run(port=port, host=host_name))
    server.start()



    initiate("ITEM1", [2,2,2], 12345)
    sleep(2)
    register("ITEM1", 12345)
    sleep(2)
    set_area([-1,-1,100,100])
    sleep(1)
    new_task("ITEM1", [[4,4,2,0],[3,7,2,1],[10,10,3,1]], 12345)
    sleep(3)
    start("ITEM1", 1, 12345)
    sleep(30)
    sign_out("ITEM1", 12345)
    sleep(1)

    # stop
    server.terminate()
    server.join()
    
    events_log = []
    try:
        # read
        while True:
            event = global_events_log.get_nowait()
            events_log.append(event)
    except Exception as _:
        # no events
        pass
        
    #print(f"list: {events_log}")
    assert len(events_log) > 20
    assert events_log[random.randint(0,len(events_log))]['token'] != ''
    x_reached = False
    y_reached = False
    z_reached = False

    for i in events_log:
        if i['coordinate_x'] > 9: 
            x_reached = True
        if i['coordinate_y'] > 9: 
            y_reached = True    
        if i['coordinate_z'] == 3: 
            z_reached = True
    assert (x_reached & y_reached & z_reached) == True
    assert ((abs(events_log[len(events_log)-1]['coordinate_x'] - 2) <= 1) & (abs(events_log[len(events_log)-1]['coordinate_y'] - 2) <= 1)) == True






