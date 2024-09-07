import time
import cv2
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.aruco.ArucoDetector import ArucoDetector
from app.aruco.ArucoCentralizer import ArucoCentralizer
from app.aruco.ArUcoDeliverySystem import ArUcoDeliverySystem
from app.servo.ServoController import ServoController



class TaskFour:
    def __init__(self) -> None:
        self.drone = Drone()
        self.camera = Camera()  # Assumindo que você tenha uma classe Camera
        self.aruco_detector = ArucoDetector()
        self.aruco_centralizer = ArucoCentralizer(self.drone, self.camera)
        self.aruco_id = 100

        #self.delivery_system = ArUcoDeliverySystem(self.drone, self.camera)
        self.camera_type = 'rtsp'
        
        self.target_lat = -14.3024719 # Latitude para colocar a armadilha
        self.target_long = -42.6896867 # Longitude para colocar a armadilha
        self.target_altitude = None

        #self.altitude_above_start = altitude_above_start
        self.starting_lat, self.starting_long, self.starting_alt = None, None, None

       

    def run(self):
        ALT_DRONE = 12
        CETEIA_LAT = -14.301307953176238
        CETEIA_LONG = -42.690438622705756
        try:
            print("+ ========= INICIANDO TASK 4 ========= +")
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return
            
            self.starting_lat, self.starting_long, self.starting_alt = self.drone.get_gps_position()

            self.drone.set_home(CETEIA_LAT, CETEIA_LONG)
            #self.drone.set_home(self.starting_lat, self.starting_long)

            self.drone.change_to_guided_mode()
            self.drone.arm_drone()
            self.drone.ascend(ALT_DRONE)
            print(f"Chegou na altitude de {ALT_DRONE} ")

            success = self.drone.move_to_position(self.target_lat, self.target_long)
            if not success:
                print(f"Falha ao chegar à coordenada ({self.target_lat}, {self.target_long}). Abortando missão.")
                return

            print(f"Chegou à coordenada alvo: Latitude {self.target_lat}, Longitude {self.target_long}, Altitude {self.target_altitude}")
            
            print("Aguarde 5 segundos")
            time.sleep(5)

            # Passo 1: Centralizar e descer para 6 metros
            self.perform_step_one()

            # Passo 2: Centralizar e descer para 0.5 metros
            self.perform_step_two()

            # Passo 3: Liberar a armadilha e retornar para a posição inicial
            print("Liberando armadilha...")
            self.drone.release_trap()
            print("Retornando para a posição inicial...")
            self.drone.return_to_home()



        except KeyboardInterrupt as e:
            #self.drone.land()
            #self.drone.disarm()
            print(e)

        except Exception as e:
            print(e)

        finally:
            #pass
            self.drone.land()
            self.drone.disarm()

    
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
        while attempts < max_attempts and not aruco_found:
            print(f"Tentativa {attempts+1}/{max_attempts}")
            self.camera.read_capture()
            self.aruco_centralizer.display_video()
            
            ids, centers = self.aruco_centralizer.detect_and_process_arucos()
            self.aruco_centralizer.draw_reference_square()

            if ids is not None and self.aruco_id in ids:
                print("ArUco encontrado, tentando centralizar.")
                center_index = list(ids).index(self.aruco_id)
                center = centers[center_index]
                offset_x, offset_y = self.aruco_centralizer.calculate_offset(center, self.camera.frame.shape)
                distance_pixels = (offset_x**2 + offset_y**2)**0.5
                color = self.aruco_centralizer.GREEN if distance_pixels <= self.aruco_centralizer.INTEREST_REGION_PIXELS else self.aruco_centralizer.RED

                # Se a centralização for bem-sucedida, ajusta a altitude e finaliza
                if self.aruco_centralizer.adjust_drone_position(center, offset_x, offset_y, distance_pixels, color):
                    print(f"Ajustando altitude para {target_altitude} metros...")
                    self.drone.descend(target_altitude)
                    aruco_found = True  # Marca que o ArUco foi encontrado e centralizado
            else:
                print("ArUco não encontrado nesta tentativa.")

            #self.aruco_centralizer.display_video()
            attempts += 1

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

    def perform_step_two(self, target_altitude: float = 0.5):
        """
        Realiza o passo 2: Centraliza o ArUco novamente e ajusta a altitude do drone para 0.5 metros.
        """
        print(f"Iniciando passo 2: Centralização e ajuste de altitude para {target_altitude} metros.")
        while not self.centralize_and_adjust_altitude(target_altitude):
            pass
        print("Passo 2 concluído.")


trap_lat = -14.3022984
trap_long = -42.6900696
task = TaskFour()
task.run()
