import time
import threading
import requests
import json
import math
import os

CONTENT_HEADER = {"Content-Type": "application/json"}
ATM_ENDPOINT_URI = "http://atm:6064/data_in"
ATM_WATCHDOG_URI = "http://atm:6064/watchdog"
ATM_SIGN_UP_URI = "http://atm:6064/sign_up"
ATM_SIGN_OUT_URI = "http://atm:6064/sign_out"
FPS_ENDPOINT_URI = "http://fps:6065/data_in"
DELIVERY_INTERVAL_SEC = 1


class Drone:

    def __init__(self, coordinate, name, psswd):
        self.start_point = coordinate[:]
        self.coordinate = coordinate
        self.name = name
        self.psswd = psswd  
        self.emergency_stop = threading.Event()
        self.token = ''
        self.motion_status = "Stopped"
        self.task_points = []
        self.camera_status = "OFF"
        self.camera_event = threading.Event()
        self.battery_charge = 100
        self.status = 'Active'
        self.hash = ''
        self.watchdog_time = time.time()

        # threading.Thread(
        #             target=lambda:  self.self_diagnostic()).start()
        # threading.Thread(
        #             target=lambda:  self.position_controller()).start()

        


    def get_coordinate(self):
        return self.coordinate
    
    def position_controller(self):
        if len(self.task_points) != 0:
            if self.task_points[0][3] == 1 and self.camera_status == 'OFF':
                self.telemetry_status_set('ON')
            elif self.task_points[0][3] != 1 and self.camera_status == 'ON':
                self.telemetry_status_set('OFF')
        if (abs(self.coordinate[0] - self.start_point[0]) < 1) and (abs(self.coordinate[1] - self.start_point[1]) < 1) and len(self.task_points) == 0:
            self.end_task()
        
    def end_task(self):
        try:
            self.camera_event.set()
            data = {
            "name": self.name,
            "operation": "log",
            "msg": "Task finished"
            }
            response = requests.post(
                FPS_ENDPOINT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
        except Exception as e:
            print(f'exception raised: {e}')

        

    def move_to(self, x, y, z, speed):
        self.motion_status = "Active"
        global DELIVERY_INTERVAL_SEC
        dx_target = x - self.coordinate[0]
        dy_target = y - self.coordinate[1]
        dz_target = z - self.coordinate[2]
        direction = math.atan2(dy_target, dx_target)
        t = math.sqrt(dx_target**2 + dy_target**2)/speed
        time_offset = t%DELIVERY_INTERVAL_SEC

        while not self.emergency_stop.is_set():
            if abs(self.coordinate[2] - z) >= 1:
                time.sleep(1)
                if (self.coordinate[2] - z) >= 0:
                    self.coordinate[2] -= 1
                else: 
                    self.coordinate[2] += 1
                self.send_position()
            else:
                if time_offset == 0:
                    if (abs(self.coordinate[0] - x) > 1) or (abs(self.coordinate[1] - y) > 1):
                        time.sleep(DELIVERY_INTERVAL_SEC)
                        self.coordinate[0] += math.cos(direction) * speed * DELIVERY_INTERVAL_SEC
                        self.coordinate[1] += math.sin(direction) * speed * DELIVERY_INTERVAL_SEC
                        self.send_position()
                    else:
                        self.emergency_stop.set()
                        self.motion_status = "Stopped"
                        print(f'[REACHED_POINT] {self.coordinate}')
                else:
                    if (abs(self.coordinate[0] - x) > 1) or (abs(self.coordinate[1] - y) > 1):
                        time.sleep(time_offset)
                        self.coordinate[0] += math.cos(direction) * speed * DELIVERY_INTERVAL_SEC
                        self.coordinate[1] += math.sin(direction) * speed * DELIVERY_INTERVAL_SEC
                        self.send_position()
                    else:
                        self.emergency_stop.set()
                        self.motion_status = "Stopped"
                        print(f'[REACHED_POINT] {self.coordinate}')
                    time_offset=0
            self.battery_charge -= 1
            self.self_diagnostic()
            self.position_controller()
            self.watchdog()


    def clear_emergency_flag(self):
        if not self.status == "Blocked":
            self.emergency_stop.clear()

    def self_diagnostic(self):
        if self.battery_charge < 20:
            print(f'[BATTRE_LOW]')
            print (self.battery_charge)
            
    def watchdog(self):
        if (time.time() - self.watchdog_time) > 2:
            try:
                data = {}
                response = requests.post(
                    ATM_WATCHDOG_URI,
                    data=json.dumps(data),
                    headers=CONTENT_HEADER,
                )
                #content = response.content.decode.json
                content = response.json()
                print(content)
                #print(response.content.decode())
                print(content['time'])
                self.watchdog_time = content['time']
            except Exception as e:
                print(e)
        if (time.time() - self.watchdog_time) > 10:
            self.emergency()
        
    def telemetry_status_set(self, status):
        if status == 'OFF':
            self.camera_status = 'OFF'
            self.camera_event.set()
            print(f'[DRONE_CAMERA_OFF]')
        elif status == 'ON': 
            self.camera_status = 'ON'
            self.camera_event.clear()
            threading.Thread(
                    target=lambda:  self.telemetry()).start()
            

    def telemetry(self):

        print(f'[DRONE_CAMERA_ON]')
        while not self.camera_event.is_set():
            time.sleep(DELIVERY_INTERVAL_SEC)
            
            percent = 0
            if os.path.exists("/storage/tmp.jpeg"):
                im = Image.open("tmp.jpeg")
                pixels = im.load()  # список с пикселями
                x, y = im.size  # ширина (x) и высота (y) изображения

                white_pix = 0
                another_pix = 0

                for i in range(x):
                    for j in range(y):
                        for q in range(3):
                            # проверка чисто белых пикселей, для оттенков нужно использовать диапазоны
                            if pixels[i, j][q]  > 240: #!= 255:  # pixels[i, j][q] > 240  # для оттенков
                                another_pix += 1
                            else:
                                white_pix += 1

                try:
                    percent = round(white_pix / another_pix * 100, 3)
                    print(percent)
                except ZeroDivisionError:
                    print("Белых пикселей нет")

            try:
                data = {
                "name": self.name,
                "operation": "data",
                "percent": percent
                }
                response = requests.post(
                    FPS_ENDPOINT_URI,
                    data=json.dumps(data),
                    headers=CONTENT_HEADER,
                )
                #print(f"[info] результат отправки данных: {response}")
            except Exception as e:
                print(f'exception raised: {e}')

    def change_echelon(self, new_echelon):
        self.emergency()
        self.move_to(self.coordinate[0],self.coordinate[1], new_echelon, 1)
        #self.start()

    def start(self, speed):
        self.clear_emergency_flag()
        self.camera_event.clear()
        while not len(self.task_points) == 0:
            x = self.task_points[0][0]
            y = self.task_points[0][1]
            z = self.task_points[0][2]
            if not self.emergency_stop.is_set() and self.motion_status=="Stopped":
                # print(f'[DRONE_DEBUG] asked motion to {x,y,z}')
                threading.Thread(
                    target=lambda:  self.move_to(x,y,z,speed)).start()
            else:
                if abs(self.coordinate[0] - x) <= 1 and abs(self.coordinate[1] - y) <= 1 and abs(self.coordinate[2] - z) <= 1:
                    self.task_points.pop(0)
                    self.clear_emergency_flag()
                time.sleep(DELIVERY_INTERVAL_SEC)
        
        if len(self.task_points) == 0: # return to home
            time.sleep(DELIVERY_INTERVAL_SEC)
            self.clear_emergency_flag()
            threading.Thread(
                    target=lambda:  self.move_to(self.start_point[0],self.start_point[1],self.start_point[2],1)).start()
            
    def stop(self):
        self.emergency()
        
    def sign_out(self):
        self.emergency()
        data = {
            "name": self.name
            }
        try:
            response = requests.post(
                ATM_SIGN_OUT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
        except Exception as e:
            print(f'exception raised: {e}')

    def register(self):
        data = {
            "name": self.name,
            "coordinate": self.coordinate,
            "status": "OK",
            "index": int(os.environ['DRONE_PORT']) - 6066,
            "port": os.environ['DRONE_PORT']
            }
        try:
            response = requests.post(
                ATM_SIGN_UP_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
        except Exception as e:
            print(f'exception raised: {e}')

    def send_position(self):
        data = {
            "name": self.name,
            "token": self.token,
            "coordinate": self.coordinate,
            "coordinate_x": self.coordinate[0],
            "coordinate_y": self.coordinate[1],
            "coordinate_z": self.coordinate[2]
            }
        try:
            response = requests.post(
                ATM_ENDPOINT_URI,
                data=json.dumps(data),
                headers=CONTENT_HEADER,
            )
        except Exception as e:
            print(f'exception raised: {e}')

    def emergency(self):
        self.emergency_stop.set()
        self.motion_status = "Stopped"
        time.sleep(DELIVERY_INTERVAL_SEC)
        self.send_position()
