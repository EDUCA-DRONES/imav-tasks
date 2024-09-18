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
        self.TASK_TWO_BEGIN_ARUCO = 200
        self.TASK_TWO_END_ARUCO = 200
        self.TASK_THREE_ARUCO = 302
        self.TASK_FOUR_ARUCO = 302
        self.speedMps = 0.5
        self.cmMovimenters = self.cmMovimenters
      
    def taskOne(self):
        self.drone.ascend(1.5)  
        print('subiu')
        
        for i in range(16):
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
                self.drone.move_forward(self.speedMps) 
        
        for i in range(5):
            self.fileManager.create_image(
                self.cameraRasp.frame,
                self.drone.current_altitude(),
                i
            )
            
    def taskTwo(self):
        self.drone.descend(1.2)
        self.drone.rotate_yaw(90)
        
        for i in range(13):
            self.camera.initialize_video_capture(self.IPCAM)
            self.camera.read_capture()
            images, ids, corner = self.arucoDetector.detect_arucos(self.camera.frame)
            if ids is not None and self.TASK_TWO_END_ARUCO in ids:
                self.drone.move_forward(0.8) 
                break
            else:
                print('mexendo')
                self.drone.move_forward(self.speedMps) 
    
    def taskThree(self):
        self.drone.ascend(1.7)
        for i in range(12):
            self.camera.initialize_video_capture(self.IPCAM)
            self.camera.read_capture()
            images, ids, corner = self.arucoDetector.detect_arucos(self.camera.frame)
            if ids is not None and self.TASK_THREE_ARUCO in ids:
                break
            else:
                print('mexendo')
                self.drone.move_forward(self.speedMps) 
          
    def taskFour(self):
        self.drone.rotate_yaw(90)
        for i in range(6):
            self.camera.initialize_video_capture(self.IPCAM)
            self.camera.read_capture()
            images, ids, corner = self.arucoDetector.detect_arucos(self.camera.frame)
            if ids is not None and self.TASK_THREE_ARUCO in ids:
                break
            else:
                print('mexendo')
                self.drone.move_forward(self.speedMps) 
          
    def run(self) -> None:
        try:
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return
            
            self.drone.change_to_guided_mode()
        
            self.drone.arm_drone()
            self.taskOne()
            self.taskTwo()
            self.taskThree()
                        
        except KeyboardInterrupt as e:
            print(e)
            print(e.with_traceback())

        except Exception as e:
            print(e)
            print(e.with_traceback())
        finally:
            self.drone.land()
            self.drone.disarm()
indoor = Indoor()
indoor.run()
