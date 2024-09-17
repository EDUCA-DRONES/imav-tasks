from missions.outdoor import Task
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera

class TaskOne(Task.Task): 
    
    def __init__(self) -> None:
        print('Mission 1')
        self.drone = Drone()
        self.camera = Camera()
        self.camera_type = 'computer'

        self.coordinates = [
            (51.4033710, -2.8194634), 
            (51.4048087, -2.8167029), 
            (51.4041240, -2.8158278), 
            (51.4026983, -2.8185450)
        ]

    def run(self):
        try:
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return

            self.drone.change_to_guided_mode()

            starting_lat, starting_long, _ = self.drone.get_gps_position()
           
            self.camera.initialize_video_capture(self.camera_type)

            self.drone.set_home(starting_lat, starting_long)
            self.drone.arm_drone()
            self.drone.ascend(20)
            
            for round in range(3):
                for coord in self.coordinates:
                    lat, long = coord
                    self.drone.move_to_position(lat, long, 20)
            
        except KeyboardInterrupt as e:
            print(e)

        except Exception as e:
            print(e)

        finally:
            self.drone.return_to_home()
            
      
              
