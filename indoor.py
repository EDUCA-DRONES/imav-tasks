from app.aruco.ArucoDetector import ArucoDetector
from app.camera.Camera import Camera
from app.drone.Drone import Drone
from app.files.FileManager import FileManager
from app.servo.ServoController import ServoController


class Indoor:
    def __init__(self) -> None:
        self.drone = Drone()
        self.camera = Camera()
        self.cameraRasp = Camera()
        self.servo = ServoController(self.drone)
        self.arucoDetector = ArucoDetector()
        self.fileManager = FileManager('imgs/indoor/img', 'imgs/indoor/meta')
        self.IPCAM = 'rtsp'
        self.RASPBERRY = 'imx'
        self.TASK_ONE_ARUCO = 105
      
    def taskOne(self):
        self.drone.ascend(1.5)  
        print('subiu')
        
        for i in range(13):
            self.camera.initialize_video_capture(self.IPCAM)
            self.camera.read_capture()
            images, ids, corner = self.arucoDetector.detect_arucos(self.camera.frame)
            if ids is not None and self.TASK_ONE_ARUCO in ids:
                print('tirando foto')
                self.cameraRasp.initialize_video_capture(self.RASPBERRY)
                self.cameraRasp.read_capture()
                for i in range(5):
                    self.fileManager.create_image(
                        self.cameraRasp.frame,
                        self.drone.current_altitude(),
                        i
                    )
                
                break
            else:
                print('mexendo')
                self.drone.move_forward(0.3, 0.5) 
        
        for i in range(5):
            self.fileManager.create_image(
                self.cameraRasp.frame,
                self.drone.current_altitude(),
                i
            )
            
    def taskTwo(self):
        pass
              
    def run(self) -> None:
        try:
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return
            
            self.drone.change_to_guided_mode()
        
            self.drone.arm_drone()
            self.taskOne()
            self.drone.rotate_yaw(90)
            
        except KeyboardInterrupt as e:
            print(e)
            print(e.with_traceback())

        except Exception as e:
            print(e)
            print(e.with_traceback())
        
indoor = Indoor()
indoor.run()
