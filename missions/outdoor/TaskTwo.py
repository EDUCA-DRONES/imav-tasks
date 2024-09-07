from datetime import datetime
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.files.FileManager import FileManager
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
        
        self.camera_type = 'computer'
        self.territory_x = 20
        self.territory_y = 20
            
        self.camera_delay = 0.25
        
    def run(self):
        try:
            x_loop = int(abs(self.territory_x / self.drone.config.x_meters_cover))
            y_loop = int(abs(self.territory_y / self.drone.config.y_meters_cover))
            
            if not self.drone.connected():
                    print("Falha ao conectar com o drone.")
                    return

            self.drone.change_to_guided_mode()
            
            starting_lat, starting_long, _ = self.drone.get_gps_position()

            print(starting_lat, starting_long)
            
            self.camera.initialize_video_capture(self.camera_type)
            
            self.drone.set_home(starting_lat, starting_long)
            self.drone.arm_drone()
            self.drone.ascend(12)
            
            is_front = True
            count = 1
            for x in range(1, x_loop + 1):
                if x != 1:
                    self.move_drone(self.drone.config.x_meters_cover * 2, 0)
                    
                for y in range(1, y_loop + 1):
                    if is_front:
                        self.take_photos(count)
                        self.move_drone(0, self.drone.config.y_meters_cover)
                        self.take_photos(count)
                        self.move_drone(0, self.drone.config.y_meters_cover)
                    else:
                        self.take_photos(count)
                        self.move_drone(0, -self.drone.config.y_meters_cover)
                        self.take_photos(count)
                        self.move_drone(0, -self.drone.config.y_meters_cover)
                        
                    count = count + 1
                is_front = not is_front
        
        except KeyboardInterrupt as e:
            print(e)
                
        except Exception as e:
            print(e)
            
        finally:
            self.drone.return_to_home()
             
    
    def move_drone(self, x, y):
        x = x /  2 if x != 0 else 0
        y = y /  2 if y != 0 else 0
        
        self.drone.adjust_position(-x, -y)
        
    def take_photos(self, count):
        time.sleep(self.camera_delay)
        print(self.drone.get_gps_position())
        self.camera.read_capture()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.camera.save_image(f'imgs/map/img-{count}-{timestamp}.jpg')
        lat, long, alt = self.drone.get_gps_position()
        self.file_manager.create_meta_data(lat, long, alt, self.drone.current_altitude(),count)
        
        
      
      
