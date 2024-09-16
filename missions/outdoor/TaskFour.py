import time
import cv2
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.aruco.ArucoDetector import ArucoDetector
from app.aruco.ArucoCentralizer import ArucoCentralizer
from app.aruco.ArUcoDeliverySystem import ArUcoDeliverySystem
from app.servo.ServoController import ServoController
from missions.outdoor import Task

class TaskFour(Task.Task):
    def __init__(self) -> None:
        print('Mission 4')
        self.drone = Drone()
        self.camera = Camera()  # Assumindo que você tenha uma classe Camera
        self.aruco_detector = ArucoDetector()
        self.aruco_centralizer = ArucoCentralizer(self.drone, self.camera)
        self.aruco_id = 800
        self.servo = ServoController(self.drone)

        #self.delivery_system = ArUcoDeliverySystem(self.drone, self.camera)
        self.camera_type = 'computer'
        
        #self.target_lat = -14.3024719 # Latitude para colocar a armadilha
        #self.target_long = -42.6896867 # Longitude para colocar a armadilha
        
        self.target_lat = -14.3014358
        self.target_long = -42.6902904
        self.target_altitude = 30

        self.target_pre_step_altitude = 7.0

        #self.altitude_above_start = altitude_above_start
        self.starting_lat, self.starting_long, self.starting_alt = None, None, None       

    def run(self):

        try:
            print("+ ========= INICIANDO TASK 4 ========= +")
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return
            
            self.starting_lat, self.starting_long, self.starting_alt = self.drone.get_gps_position()

            self.drone.set_home(self.starting_lat, self.starting_long)

            self.drone.change_to_guided_mode()
            self.drone.arm_drone()
            self.drone.ascend(self.target_altitude)
            print(f"Chegou na altitude de {self.target_altitude} ")

            success = self.drone.move_to_position(self.target_lat, self.target_long)
            if not success:
                print(f"Falha ao chegar à coordenada ({self.target_lat}, {self.target_long}). Abortando missão.")
                return

            print(f"Chegou à coordenada alvo: Latitude {self.target_lat}, Longitude {self.target_long}, Altitude {self.target_altitude}")
            
            print("Aguarde 5 segundos")
            time.sleep(5)

            # Descer para 7 metros antes de executar o passo 1
            
            print(f"Ajustando altitude para {self.target_pre_step_altitude} metros antes de procurar o ArUco...")
            self.drone.descend(self.target_pre_step_altitude)

            if not self.drone.wait_until_altitude_reached(self.target_pre_step_altitude):
                print(f"Falha ao atingir a altitude de {self.target_pre_step_altitude} metros. Abortando...")
                return

            # Passo 1: Centralizar e descer para 6 metros
            self.perform_step_one()

            # Passo 2: Centralizar e descer para 0.5 metros
            self.perform_step_two()

            # Passo 3: Liberar a armadilha e retornar para a posição inicial
            print("Liberando armadilha...")
            self.servo.release_trap()
            print("Retornando para a posição inicial...")



        except KeyboardInterrupt as e:
            #self.drone.land()
            #self.drone.disarm()
            print(e)

        except Exception as e:
            print(e)

        finally:
            # pass
            # self.drone.land()
            # self.drone.disarm()
            self.drone.return_to_home()

    
    def centralize_and_adjust_altitude(self, target_altitude: float, max_attempts: int = 10) -> bool:
        """
        Centraliza o ArUco na imagem e ajusta a altitude do drone até a altitude desejada.
        Tentará centralizar por 'max_attempts' antes de desistir.
        Retorna True se o ArUco foi centralizado e o drone ajustou a altitude, caso contrário, False.
        """
        self.camera.initialize_video_capture(self.camera_type)
        
        attempts = 0
        aruco_found = False

        # Tenta encontrar e centralizar o ArUco até o número máximo de tentativas
        while True and not aruco_found:
            #print(f"Tentativa {attempts+1}/{max_attempts}")
            self.camera.read_capture()
            #print("self.camera.read_capture() executado")
            
            ids, centers = self.aruco_centralizer.detect_and_process_arucos()
            self.aruco_centralizer.draw_reference_square()
            # self.aruco_centralizer.display_video()

            # print(f"ids: {ids}")
            #print("Seis segundos até a próxima tentativa \n")
            #time.sleep(6)
            if ids is not None:
                print(f"IDs detectados: {ids}")
                if self.aruco_id in ids:

                    print("ArUco encontrado, tentando centralizar.")
                    center_index = list(ids).index(self.aruco_id)
                    center = centers[center_index]
                    offset_x, offset_y = self.aruco_centralizer.calculate_offset(center, self.camera.frame.shape)
                    distance_pixels = (offset_x**2 + offset_y**2)**0.5
                    color = self.aruco_centralizer.GREEN if distance_pixels <= self.aruco_centralizer.INTEREST_REGION_PIXELS else self.aruco_centralizer.RED

                    # Debug: Verificar o que o método adjust_drone_position está retornando
                    adjustment_success = self.aruco_centralizer.adjust_drone_position(center, offset_x, offset_y, distance_pixels, color)
                    print(f"Ajuste do drone bem-sucedido: {adjustment_success}")

                    # Se a centralização for bem-sucedida, ajusta a altitude e finaliza
                    if adjustment_success:
                        current_altitude = self.drone.current_altitude()
                        print(f"Altura atual do drone: {current_altitude}")

                        print(f"Ajustando altitude para {target_altitude} metros...")
                        self.drone.descend(target_altitude)
                        aruco_found = True  # Marca que o ArUco foi encontrado e centralizado

                        #print("Pegando coordenadas ao centralizar o aruco")
                        #aruco_center_img_lat, aruco_center_img_lon, aruco_center_img_alt = self.drone.get_gps_position()
                        
                        #self.drone.move_to_position(aruco_center_img_lat, aruco_center_img_lon)
                        # Verifica se a altitude foi atingida antes de prosseguir
                        if not self.drone.wait_until_altitude_reached(target_altitude):
                            print(f"Falha ao atingir a altitude de {target_altitude} metros. Abortando...")
                            return False
             
                else:
                    print("ArUco id 100 não detectado nesta tentativa.")
            else:
                print("Nenhum ArUco não encontrado nesta tentativa.")

            #self.aruco_centralizer.display_video()
            attempts += 1

        self.camera.release_video_capture()
        if aruco_found:
            print("Centralização e ajuste de altitude completos.")
            return True
        else:
            print("Falha ao encontrar ou centralizar o ArUco após várias tentativas.")
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

    def perform_step_two(self, target_altitude: float = 1.5):
        """
        Realiza o passo 2: Centraliza o ArUco novamente e ajusta a altitude do drone para 0.5 metros.
        """
        print(f"Iniciando passo 2: Centralização e ajuste de altitude para {target_altitude} metros.")
        while not self.centralize_and_adjust_altitude(target_altitude):
            pass
        print("Passo 2 concluído.")
 