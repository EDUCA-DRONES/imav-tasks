from datetime import datetime, timezone
from app.files.Reports import FlightLogger
from missions.outdoor import Task
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera

class TaskOneClient(Task.Task): 
    
    def __init__(self) -> None:
        print('Mission 1')
        self.drone = Drone()
        self.camera = Camera()
        self.logger = FlightLogger('perfomance.csv')
        self.logger.initialize_log_file()
        self.logger
        self.camera_type = 'rtsp'

    def run(self):
        if not self.drone.connected():
            print("Falha ao conectar com o drone.")
            return
        
        while True:
            try:

                lat, long, _ = self.drone.get_gps_position()
                alt = self.drone.current_altitude()
                voltage, current = self.drone.get_battery_voltage_and_current()
                self.logger.log_performance(lat, long, alt, voltage, current)
                time.sleep(5)

            except Exception as e:
                print(e)
                pass
            

            
 