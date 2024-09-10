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

class TaskOne(Task.Task):
    """
    **Tarefa 1: Captura de Tela (Identificação Manual):**

    Nesta tarefa, o MAV deve iniciar a partir da zona de partida, levantar voo automaticamente e transitar para a primeira zona de tarefa, onde uma tela com uma imagem será identificada e capturada. O MAV deve capturar uma imagem da tela a 1,5 metros acima do chão. A identificação da imagem será feita manualmente após a conclusão da missão.

    O ponto de captura será identificado com o marcador ArUco 5x5 ID 105 na base. O monitor estará aproximadamente 90 graus à esquerda do drone quando o marcador for visualizado.
    """

    def __init__(self) -> None:
        print('Mission 1')
        self.drone = Drone()
        self.file_manager = FileManager('imgs/task1/img', 'imgs/task1/meta')
        self.file_manager.create_base_dirs()
        self.camera = Camera()

        self.camera_type = 'computer'
        self.zone_marker_id = 105  # ID do marcador ArUco para identificação da tela
        self.capture_height = 1.5  # Altura de captura em metros
        self.camera_delay = 0.25
        self.images_to_capture = 5

        # Inicializa os detectores
        self.aruco_detector = ArucoDetector()
        self.aruco_centralizer = ArucoCentralizer(self.drone, self.camera)

        self.follow_tape = FollowTape(self.drone, self.camera)

    def run(self):
        try:
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return

            self.drone.change_to_guided_mode()
            starting_lat, starting_long, _ = self.drone.get_gps_position()
            print(f"Posição inicial: {starting_lat}, {starting_long}")

            self.camera.initialize_video_capture(self.camera_type)

            # Levanta voo e move para a zona de tarefa
            self.drone.set_home(starting_lat, starting_long)
            self.drone.arm_drone()
            self.drone.ascend(self.capture_height + 2)  # Subir um pouco mais para garantir a segurança
            #self.drone.move_to_marker(self.zone_marker_id)

            print("Iniciando a tarefa de seguir a fita azul...")
            self.follow_tape.follow_tape()
            
            print("Detectando o marcador ArUco ID 105...")
            if self.detect_marker(self.zone_marker_id):
                print("Marcador detectado. Centralizando o drone...")
                self.centralize_drone()

                print("Girando o drone 90 graus à esquerda...")
                self.drone.rotate_yaw(-90)  # Girar 90 graus para a esquerda

                print("Capturando imagens do monitor...")
                for i in range(self.images_to_capture):
                    self.capture_image(i + 1)

                print("Finalizando a missão com uma rotação de 180 graus...")
                self.drone.rotate_yaw(180)  # Girar 180 graus para finalizar a missão

                print("Aqui deve seguir para a TaskTwo da indoor")
                #   self.follow_tape.follow_tape()
           
                

        except KeyboardInterrupt as e:
            print(e)

        except Exception as e:
            print(e)

        finally:
            print("Finally - Seguir para TaskTwo indoor")
            #pass
            self.drone.land()
            self.drone.disarm()
            # Aqui o drone deve prosseguir para a próxima tarefa, a TaskTwo da indoor 
            self.drone.return_to_home()
            print("Missão concluída. Retornando à zona de partida.")

    def detect_marker(self, marker_id):
        """
        Detecta o marcador ArUco com o ID fornecido e realiza a movimentação necessária.
        """
        while True:
            self.camera.read_capture()
            image, ids, _ = self.aruco_detector.detect_arucos(self.camera.frame)
            if ids is not None and marker_id in ids:
                return True
                

    def centralize_drone(self):
        """
        Centraliza o drone com base na posição do marcador ArUco e alinha com o monitor.
        """
        marker_id = self.zone_marker_id  # Certifique-se de usar o ID correto aqui
        while True:
            self.camera.read_capture()
            ids, centers = self.aruco_centralizer.detect_and_process_arucos()
            if ids is not None and marker_id in ids:
                center = centers[ids.index(marker_id)]
                offset_x, offset_y = self.aruco_centralizer.calculate_offset(center, self.camera.frame.shape)
                distance_pixels = (offset_x**2 + offset_y**2)**0.5
                if self.aruco_centralizer.adjust_drone_position(center, offset_x, offset_y, distance_pixels, self.aruco_centralizer.RED):
                    break

            # Adiciona uma pausa para evitar loop excessivo
            time.sleep(0.5)

    def capture_image(self, image_number):
        time.sleep(self.camera_delay)
        self.camera.clean_buffer()
        self.camera.read_capture()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        img_name = f'imgs/indoor/task1/img-monitor-{image_number}-{timestamp}.jpg'
        self.camera.save_image(img_name)
        print(f"Imagem capturada: {img_name}")
        lat, long, alt = self.drone.get_gps_position()
        self.file_manager.create_meta_data(lat, long, alt, self.drone.current_altitude(), timestamp)

