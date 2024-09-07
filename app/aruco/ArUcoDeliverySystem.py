from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.aruco.ArucoDetector import ArucoDetector
from app.aruco.ArucoCentralizer import ArucoCentralizer
import time

class ArUcoDeliverySystem:
    def __init__(self, drone, camera) -> None:
        self.drone = drone
        self.camera = camera
        self.aruco_id = 100
        self.aruco_detector = ArucoDetector()
        self.aruco_centralizer = ArucoCentralizer(self.drone, self.camera)

    def centralize_and_adjust_altitude(self, target_altitude: float) -> bool:
        """
        Centraliza o ArUco na imagem e ajusta a altitude do drone até a altitude desejada.
        Retorna True se o ArUco foi centralizado e o drone ajustou a altitude, caso contrário, False.
        """
        self.camera.read_capture()
        ids, centers = self.aruco_centralizer.detect_and_process_arucos()
        self.aruco_centralizer.draw_reference_square()

        if ids is not None and self.aruco_id in ids:
            center_index = list(ids).index(self.aruco_id)
            center = centers[center_index]
            offset_x, offset_y = self.aruco_centralizer.calculate_offset(center, self.camera.frame.shape)
            distance_pixels = (offset_x**2 + offset_y**2)**0.5
            color = self.aruco_centralizer.GREEN if distance_pixels <= self.aruco_centralizer.INTEREST_REGION_PIXELS else self.aruco_centralizer.RED

            if self.aruco_centralizer.adjust_drone_position(center, offset_x, offset_y, distance_pixels, color):
                print(f"Ajustando altitude para {target_altitude} metros...")
                self.drone.adjust_altitude(target_altitude)
                return True

        self.aruco_centralizer.display_video()
        return False

    def perform_step_one(self, target_altitude: float = 6.0, timeout: float = 30.0):
        """
        Realiza o passo 1: Centraliza o ArUco e ajusta a altitude do drone para 6 metros.
        """
        print("Iniciando passo 1: Centralização e ajuste de altitude para 6 metros.")
        start_time = time.time()
        while not self.centralize_and_adjust_altitude(target_altitude):
            if time.time() - start_time > timeout:
                print("Tempo esgotado para o passo 1. Não foi possível centralizar o drone.")
                return False
        print("Passo 1 concluído.")
        return True

    def perform_step_two(self, target_altitude: float = 0.5):
        """
        Realiza o passo 2: Centraliza o ArUco novamente e ajusta a altitude do drone para 0.5 metros.
        """
        print("Iniciando passo 2: Centralização e ajuste de altitude para 0.5 metros.")
        while not self.centralize_and_adjust_altitude(target_altitude):
            pass
        print("Passo 2 concluído.")