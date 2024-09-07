from missions.outdoor import Task
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.files.FileManager import FileManager
from app.files.Reports import FlightLogger

class TaskThree(Task.Task): 
    """
    **Tarefa 3: Imagens Dinâmicas de Animais (identificação das zebras e captura de imagens):**

    Nesta tarefa, quatro waypoints devem ser alcançados em uma sequência de waypoints desconhecida a priori. Após a chegada do drone designado para a tarefa no
    waypoint de início/fim da tarefa, o juiz distribuirá uma lista de waypoints em papel consistindo de quatro waypoints no formato [latitude decimal, longitude decimal, altitude acima do ponto inicial] que devem
    ser voados sobre. Para verificar se os waypoints foram sobrevoados com sucesso, um arquivo de log CSV deve ser enviado por e-mail aos juízes no formato [Hora UTC incluindo. segundos (Formato AAAA-MM-
    DDTHH:MM:SS.sss), latitude decimal, longitude decimal, altitude acima do ponto inicial]no máximo 30 minutos após o término do intervalo de tempo.
    """

    def __init__(self) -> None:
        print('Mission 3')
        self.drone = Drone()
        self.file_manager = FileManager('imgs/zebras_data/img', 'imgs/zebras_data/meta')
        self.file_manager.create_base_dirs()
        self.camera = Camera()
        self.logger = FlightLogger()
        self.camera_type = 'computer'

        self.coordinates = [
            (-14.302302448845442, -42.69017646004376), 
            (-14.302285026476568, -42.68986360843068), 
            (-14.302172707919963, -42.69006231316129), 
            (-14.301945153268674, -42.69036187559611)
        ]

        self.starting_lat = None
        self.starting_long = None
        

    def run(self):
        ALT_DRONE = 12
       
        try:
            print("+ ========= INICIANDO TASK 3 ========= +")
            if not self.drone.connected():
                print("Falha ao conectar com o drone.")
                return
            
            self.starting_lat, self.starting_long, _ = self.drone.get_gps_position()

            self.drone.set_home(self.starting_lat, self.starting_long)

            self.drone.change_to_guided_mode()
            self.drone.arm_drone()
            self.drone.ascend(ALT_DRONE)
            print(f"Chegou na altitude de {ALT_DRONE} m")
                
            count = 1 # count é o id da zebra
            for lat, long in self.coordinates:
                print(f"Indo para a coordenada {count}")
                # Enviar o drone para as coordenadas específicas
                success = self.drone.move_to_position(lat, long)
                if not success:
                    print(f"Falha ao chegar à coordenada ({lat}, {long}). Abortando missão.")
                    return
                
                print("Aguarde 5 segundos")
                time.sleep(5)

                self.capture_image(count)
                print("Foto capturada")
                count += 1 

            # Retornar ao ponto de partida e pousar
            self.drone.return_to_home()
            
            """ success = self.drone.move_to_position(self.starting_lat, self.starting_long)
            if success:
                self.drone.land()
                self.drone.disarm()
            else:
                print("Falha ao retornar ao ponto de partida. Missão abortada.")"""
            
        except KeyboardInterrupt as e:
            print(e)
                
        except Exception as e:
            print(e)
            
        finally:
            pass
            #self.drone.land()
            #self.drone.disarm() 
            #self.drone.return_to_home()
  
    def capture_image(self, zebra_id):
        self.camera.initialize_video_capture(self.camera_type)
        time.sleep(0.3)
        
        lat, long, alt = self.drone.get_gps_position()
        print(f"Capturando imagens na coordenada: Latitude {lat}, Longitude {long}, Altitude {alt} m")

        for i in range(1, 6):
            self.camera.read_capture()
            IMAGE_NAME = f'zebra-{zebra_id}-img-{i}.jpg'
        
            self.camera.save_image(f'imgs/zebras_data/img/{IMAGE_NAME}')
            self.camera.clean_buffer()
            self.file_manager.create_meta_data(lat, long, alt, self.drone.current_altitude(), f"{zebra_id}_{i}")            
            self.logger.log_position(zebra_id, i, lat, long, alt, IMAGE_NAME)

            time.sleep(0.5)

        self.camera.release_video_capture()
        

        print(f"5 imagens capturadas e salvas para a coordenada da zebra: {zebra_id}")
      

 
