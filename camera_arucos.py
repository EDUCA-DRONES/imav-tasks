import cv2
from app.camera.Camera import Camera
from app.aruco.ArucoDetector import ArucoDetector
from app.drone.Drone import Drone
from app.aruco.ArucoCentralizer import ArucoCentralizer

def main():
    # Inicialize o drone e a câmera
    drone = Drone()
    camera = Camera()
    
    # Configure o tipo de câmera (por exemplo, 'computer', 'rtsp', 'imx', 'analog', 'esp32')
    camera_type = 'computer'
    
    # Inicializa a captura de vídeo
    camera.initialize_video_capture(camera_type)
    
    # Crie o detector ArUco
    aruco_detector = ArucoDetector()
    
    # Crie o centralizador ArUco
    aruco_centralizer = ArucoCentralizer(drone, camera)
    
    while True:
        # Capture um frame da câmera
        camera.read_capture()
        
        if not camera.ret:
            print("Falha ao capturar o vídeo.")
            break
        
        # Detecte e processe os marcadores ArUco
        image, ids, _ = aruco_detector.detect_arucos(camera.frame)
        
        if ids is not None:
            print("IDs detectados:", ids)
        else:
            print("Nenhum marcador ArUco detectado.")
        
        # Ajuste a posição do drone se necessário
        aruco_centralizer.execute()
        
        # Exiba o vídeo com os marcadores detectados
        #aruco_centralizer.display_video()
        
        # Saia do loop se a tecla 'q' for pressionada
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Libere a captura e feche todas as janelas
    camera.release_video_capture()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
