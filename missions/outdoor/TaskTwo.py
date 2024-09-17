from datetime import datetime
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.files.FileManager import FileManager
from app.ml import ZebraModel
from missions.outdoor import Task

class TaskTwo(Task.Task):
    """
    **Tarefa 2: Censo de Animais (mapeamento e identificação):**

    Nesta tarefa, as equipes terão que explorar uma área determinada e localizar o maior número possível de animais dentro dessa área, criando um mapa ortofoto para identificar onde eles estão. O mapa deve ser enviado por e-mail aos juízes até no máximo 30 minutos após o término do tempo da missão. O não cumprimento do prazo de submissão resultará na atribuição de zero pontos para este elemento da missão.

    A resolução do mapa/foto não é levada em consideração para a pontuação, mas os animais devem ser identificáveis. Um animal é contado como detectado quando está localizado a no máximo 10 metros de sua posição correta e as coordenadas em latitude e longitude decimal são fornecidas aos juízes.
    """

    def __init__(self) -> None:
        print('Mission 2')
        self.drone = Drone()
        self.file_manager = FileManager('imgs/map/img', 'imgs/map/meta')
        self.file_manager.create_base_dirs()
        self.camera = Camera()
        self.zebra_detector = ZebraModel.ZebraModel()
        
        self.camera_type = 'rtsp'
        
        # Definindo as coordenadas do terreno
        self.boundaries = {
            # "upper_left": (-14.3024023, -42.6903888), 
            # "lower_right": (-14.3036796, -42.6890734) 
            "upper_left": (51.4039735, -2.8207925), 
            "lower_right": (51.4021629, -2.8217366) 
        }
        
        self.camera_delay = 0.25

    def run(self):
    
        try:
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return

            # self.drone.change_to_guided_mode()

            # starting_lat, starting_long, _ = self.drone.get_gps_position()
           
            point_lat, point_lon = self.boundaries['upper_left']
            # print(f"Posição inicial: {starting_lat}, {starting_long}")

            # self.camera.initialize_video_capture(self.camera_type)

            # self.drone.set_home(starting_lat, starting_long)
            # self.drone.arm_drone()
            # self.drone.ascend(12)
            self.drone.descend(12)
            self.drone.move_to_position(point_lat, point_lon)
            
            is_front = True
            count = 1
            
            # Loop principal com verificação de limites
            while True:
                # Movimentação no eixo X
                  # Movimentação no eixo Y ao final de uma linha
                if  not self.is_within_longitude_boundaries() and count != 1:
                    break

                if count != 1:
                    print(f"Movendo no eixo Y, linha {count}")
                    self.move_drone(0, -self.drone.config.y_meters_cover * 2)

                    # Verifica novamente se o drone ainda está dentro dos limites após mover no eixo Y
                    if not self.is_within_longitude_boundaries():
                       
                        break

                while True:
                    self.move_in_x(is_front, count)
                    
                    adjusted = False
                    while not self.is_within_latitude_boundaries():
                        x_cover = 2
                        if is_front:
                            x_cover = -x_cover

                        self.move_drone(x_cover, 0)
                        adjusted = True
                        
                    if adjusted:
                        break

                count += 1
                is_front = not is_front
              
        except KeyboardInterrupt as e:
            print(e)

        except Exception as e:
            print(e)

        finally:
            self.drone.return_to_home()

    def move_drone(self, x, y):
        x = x / 2 if x != 0 else 0
        y = y / 2 if y != 0 else 0

        self.drone.adjust_position(-x, -y)

    def move_in_x(self, is_front, count):
        if is_front:
            x_cover = self.drone.config.x_meters_cover
        else:
            x_cover = -self.drone.config.x_meters_cover

        self.take_photos(count)

        for i in range(0,2):
            self.move_drone(x_cover, 0)
            self.take_photos(count)
            if not self.is_within_latitude_boundaries():
                return

    def take_photos(self, count):
        time.sleep(self.camera_delay)
        print(self.drone.get_gps_position())
        self.camera.clean_buffer()
        self.camera.read_capture()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        quantity = self.zebra_detector.detect(self.camera.frame)
        img_name = f'imgs/map/img/img-{str(count).zfill(2)}-{timestamp}.jpg'
        self.camera.save_image(img_name)
        print(img_name)
        lat, long, alt = self.drone.get_gps_position()
        self.file_manager.create_meta_data(lat, long, alt, self.drone.current_altitude(), count, timestamp, quantity, img_name)

    def is_within_latitude_boundaries(self):
        """
        Verifica se o drone está dentro dos limites de latitude (eixo y).
        """
        current_lat, _, _ = self.drone.get_gps_position()
        lat_upper, _ = self.boundaries["upper_left"]
        lat_lower, _ = self.boundaries["lower_right"]

        return lat_lower <= current_lat <= lat_upper

    def is_within_longitude_boundaries(self):
        """
        Verifica se o drone está dentro dos limites de longitude (eixo x).
        """
        _, current_long, _ = self.drone.get_gps_position()
        _, lon_upper = self.boundaries["upper_left"]
        _, lon_lower = self.boundaries["lower_right"]

        return lon_upper <= current_long <= lon_lower
 