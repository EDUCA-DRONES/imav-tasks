import time
import cv2
from app.drone.Drone import Drone
from app.files.FileManager import FileManager
from app.aruco.ArucoDetector import ArucoDetector
from app.files.Reports import DetectionsByAltReport
# from app.Ssh import SSHConnection


class CameraConnection:
    source = None
    
    def connection(self):
        print("Inicializando captura de vídeo...")
        return cv2.VideoCapture(int(self.source) if self.source.isdigit() else self.source)
        
class CameraRTSP(CameraConnection):
    source = 'rtsp://admin:admin@192.168.0.113:554/11'

class CameraComputer(CameraConnection):
    source = '0'

class CameraIMX519(CameraConnection):
    source = 'tcp://192.168.0.101:8554'
    
    # def connection(self):
        # host = '192.168.0.101'  # Substitua pelo endereço do seu servidor
        # port = 22  # Porta SSH
        # username = 'drone'  # Substitua pelo seu nome de usuário
        # password = 'Dron3s'  # Substitua pela sua senha
        # command = 'libcamera-vid -t 0 --inline --listen -o tcp://0.0.0.0:8554 --nopreview'

        # sshConn = SSHConnection(host, port, username, password)
        # sshConn.ssh_command(command)
        # return CameraConnection.connection(self)

class CameraESP32CAM(CameraConnection):
    source = 'http://192.168.0.115:81/stream'

class CameraAnalog(CameraConnection):
    source = '/dev/video2'

class CameraConnectionFactory():
    
    @staticmethod
    def create(type) -> CameraConnection: 
        cameras = {
            'rtsp' : CameraRTSP,
            'computer': CameraComputer,
            'imx': CameraIMX519,
            'analog': CameraAnalog,
            'esp32': CameraESP32CAM

        }
           
        return cameras[type]()

class Camera:
    def __init__(self) -> None:
      
        self.cap = None
        self.ret = None
        self.frame = None

    def initialize_video_capture(self, type):
        camera = CameraConnectionFactory.create(type)
        
        self.cap = camera.connection()
        # self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not self.cap or not self.cap.isOpened():
            print("Falha ao abrir a captura de vídeo.")
        
    def read_capture(self):
        self.ret = None
        self.frame = None
        self.ret, self.frame = self.cap.read()

       
    def capture_images_and_metadata(self, drone: Drone,  fileManager: FileManager, aruco_detector: ArucoDetector, alt, type, num_images=10, pause_time=0.5):
       
        report = DetectionsByAltReport()

        i = 0
        while True:
            i = i + 1
            if i % 5 == 0:
                answer = input('Continua? y/n')
                if answer == 'n' :
                    break;
                    
            time.sleep(pause_time)  # Espera entre capturas

            ret, frame = self.cap.read()
            processed_image, ids, __ = aruco_detector.detect_arucos(frame)
            lat, long, alt_ = drone.get_gps_position()
            
            if ret:
                detections = 0
                if ids is not None and ids.size > 0:
                    print(ids, ids.__class__)
                    detections, __ = ids.shape
                report.save_data(type, alt, detections  )
                fileManager.create_image(frame, alt, i)  
                fileManager.create_meta_data(lat, long, alt, drone.current_altitude(), i)
            
            self.clean_buffer()

        self.release_video_capture() # Libera a câmera após a captura
                    
    def clean_buffer(self):
        for _ in range(60):  
            self.cap.grab()

    def save_image(self, path):
        cv2.imwrite(path, self.frame)
    
    def release_video_capture(self): # Libera a câmera
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Captura de vídeo liberada.")