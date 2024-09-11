from datetime import datetime
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.files.FileManager import FileManager
from missions.indoor import Task
from app.drone.moves.FollowTape import FollowTape
from app.aruco.ArucoDetector import ArucoDetector
from app.aruco.ArucoCentralizer import ArucoCentralizer
import cv2



def main():
    try:
        drone = Drone()
        camera = Camera()

        if not drone.connected():
            print("Falha ao conectar com o drone.")
            return

        

        camera_type = 'computer'
        camera.release_video_capture()
        # Inicializa a captura de vídeo
        camera.initialize_video_capture(camera_type)
        #camera.display_video()

        drone.change_to_guided_mode()
        drone.arm_drone()
        drone.ascend(1.5) 
        time.sleep(4)
        
        # follow_tape = FollowTape(drone, camera)
        # follow_tape.follow_tape()
        drone.move_forward(distance_meters=5, speed_mps=1)
        #drone.move_forward(speed_mps=0.5)

        print("Aguarde 20 segundos")
        time.sleep(20)

        print("Girando yaw")
        drone.rotate_yaw(90)
       
        time.sleep(10)
        
        camera.release_video_capture()


        # Levanta voo e move para a zona de tarefa
        

    except KeyboardInterrupt as e:
        print(e)

    except Exception as e:
        print(e)

    finally:
        #pass
        drone.land()
        drone.disarm()        
    
    
    




if __name__ == "__main__":
    main()