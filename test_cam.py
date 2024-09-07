from datetime import datetime
import os
import cv2
from app.aruco.ArucoDetector import ArucoDetector
from app.camera.Camera import Camera
from app.files.FileManager import FileManager

aruco_detector = ArucoDetector()

def main():
    camera = Camera()
        
    camera.initialize_video_capture('rtsp')
    
    try:
        while True:
            camera.read_capture()
            
            camera.save_image(f'calibration_imgs/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.jpg')
            # cv2.imshow('Teste', camera.frame)
            cv2.waitKey(1)
    except:
        if camera.cap:
            camera.cap.release()
        
        cv2.destroyAllWindows()
    
    
main()