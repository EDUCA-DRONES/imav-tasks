import time
from pymavlink import mavutil
from app.drone.moves.DroneMoves import DroneMoveUPFactory
from timeit import default_timer as timer
from app.drone.tools.GPS import GPS
from app.drone.enums.Masks import POSITION, ONLY_POSITION
import math

class DroneConfig:
    def __init__(self) -> None:
        self.GUIDED_MODE = 4
        self.x_meters_cover = 6
        self.y_meters_cover = 3
        
# senha:101263
class Drone:
    def __init__(self) -> None:
        self.IP = '127.0.0.1'
        self.PORT = '14551'
        self.PROTOCOL = 'udpin'
        
        #self.IP = '192.168.0.104'
        #self.PORT = '5760'
        #self.PROTOCOL = 'tcp'
        
        self.URL = f'{self.PROTOCOL}:{self.IP}:{self.PORT}'
        self.baud = '57600'
        # self.URL = f'/dev/ttyUSB0'
        self.METER_CONVERTER = 1000.0
        self.conn =  mavutil.mavlink_connection(self.URL,baud= self.baud,  mav10=False)
        self.config = DroneConfig()
        self.velocity = 30
        self.gps = GPS()

        self.home_lat = None
        self.home_long = None
        
    def connected(self):
        return self.conn.wait_heartbeat(timeout=5)
    
    def solicit_telemetry(self):
        self.conn.mav.request_data_stream_send(self.conn.target_system, self.conn.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
        
    def current_altitude(self):
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
        if msg:
            return msg.relative_alt / self.METER_CONVERTER   # Convertendo de mm para metros
        return 0
    
    def arm_drone(self):
        print("Armando drone...")
        self.conn.mav.command_long_send(self.conn.target_system, self.conn.target_component, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
        ack = False
        while not ack:
            msg = self.conn.recv_match(type='COMMAND_ACK', blocking=True)
            ack = msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM and msg.result == 0
        print("Drone armado.")
    
    def ascend(self, target_altitude):
        current_alt = self.current_altitude()
        movement = DroneMoveUPFactory.create(current_alt, self.conn)
    
        movement.execute(target_altitude)
        
        repeat = 0
        while True:
            repeat = 1 + repeat
            current_alt = self.current_altitude()
            print(self.get_gps_position())
            self
            print(f"Altitude atual: {current_alt}m")
            if current_alt >= target_altitude * 0.95: 
                print("Altitude alvo alcançada.")
                break
            elif repeat > 20:
                print('Tentativa de comunicação excedeu o limite de tentivas... Tentando novamente.')
                self.ascend(target_altitude)
                break
    
    def descend(self, target_altitude):
        print('Descendo...')

        # Certifique-se de que o target_altitude é negativo no referencial NED
        target_altitude = abs(target_altitude)

        self.conn.mav.set_position_target_local_ned_send(
            0,  # tempo boot_ms (tempo de início do boot do sistema em milissegundos)
            self.conn.target_system,  # id do sistema
            self.conn.target_component,  # id do componente
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame de referência
            POSITION,  # tipo de máscara (indica quais dos campos são ignorados)
            0, 0, target_altitude,  # coordenadas x, y, z (em metros ou em inteiros específicos)
            0, 0, 0,  # velocidade x, y, z (em m/s)
            0, 0, 0,  # acelerações x, y, z (em m/s^2)
            0, 0  # yaw, yaw_rate (em radianos)
        )
    
    def land(self):
        print("Comando de pouso enviado ao drone.")
        
        self.conn.mav.command_long_send(
            self.conn.target_system, 
            self.conn.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        
        while True:
            print(f"Altura {self.current_altitude()}m")
            print('Descendo... \n')
            if self.current_altitude() < 0.1:
                break; 
            
        print('Desceu com crtz')
        
    
    def set_mode(self, mode):
        if mode not in self.conn.mode_mapping():
            print("Modo desconhecido:", mode)
            print("Modos disponíveis:", list(self.conn.mode_mapping().keys()))
            return

        mode_id = self.conn.mode_mapping()[mode]
        self.conn.mav.set_mode_send(
            self.conn.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id
        )

        while True:
            ack = self.conn.recv_match(type='COMMAND_ACK', blocking=True)
            ack_msg = mavutil.mavlink.enums['MAV_RESULT'][ack.result].description
            print("Modo de comando:", ack_msg)
            if ack_msg == 'ACCEPTED':
                break
        print(f"Modo alterado para {mode}")


    def disarm(self):
        print("Desarmando o drone.")
        
        self.conn.mav.command_long_send(
            self.conn.target_system, self.conn.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 0, 0, 0, 0, 0, 0, 0
        )
    
    def change_to_guided_mode(self):
        print("Mudando para modo GUIDED...")

        self.conn.mav.set_mode_send(
            self.conn.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            self.config.GUIDED_MODE  # GUIDED mode
        )

        # Aguarda confirmação de mudança de modo
        while True:
            print('entrou')
            msg = self.conn.recv_match(type='COMMAND_ACK', blocking=False)
            print(msg)
            if msg:
                print("Received msg: ", msg)
                expected_command = mavutil.mavlink.MAV_CMD_DO_SET_MODE
                expected_result = mavutil.mavlink.MAV_RESULT_ACCEPTED
                print(f"Comando esperado: {expected_command} | Resultado: {expected_result}")
                
                # Verifica se o comando corresponde ao esperado e se foi aceito
                if msg.command == 11 and msg.result == 0:
                    print("GUIDED mode set.")
                    break
                else:
                    print("Still waiting for GUIDED mode confirmation...")
                    print(f"Received command: {msg.command} | Result: {msg.result}")
   
    def get_gps_position(self):
        """
        Retrieves the current GPS position (latitude, longitude, altitude).
        """
        self.conn.mav.request_data_stream_send(
            self.conn.target_system, self.conn.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL, 1, 1
        )
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=5)
        if msg:
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt = msg.alt / 1e3
            return lat, lon, alt
        else:
            raise Exception("Failed to retrieve GPS position")

    def move(self, direction, distance, velocity=0.5):
        """
        Moves the drone in the specified direction by the specified distance at the specified velocity.
        """

        start = timer()

        print(f"Moving {direction} for {distance} meters at {velocity} m/s")
        lat, lon, alt = self.get_gps_position()
        print(f"Current GPS position: Latitude={lat}, Longitude={lon}, Altitude={alt}")
        
        new_lat, new_long =  self.gps.calculate_coord(lat, lon, 4.9, direction)
        self.go_to_coord(new_lat, new_long)
        
        print("Movement complete\n")
        end = timer()
        print(f'Duração: {end - start}')
    
    def move_north(self, distance, velocity=0.5):
        self.move('north', distance, velocity)
    
    def move_south(self, distance, velocity=0.5):
        self.move('south', distance, velocity)
    
    def move_east(self, distance, velocity=0.5):
        self.move('east', distance, velocity)
    
    def move_west(self, distance, velocity=0.5):
        self.move('west', distance, velocity)

    def go_to_coord(self, new_lat, new_long):
      
        # Enviar comando para ir para a nova coordenada
        msg = mavutil.mavlink.MAVLink_set_position_target_global_int_message(
            0,  # time_boot_ms (not used)
            0, 0,  # target system, target component
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            0b0000111111111000,  # type_mask (only positions enabled)
            int(new_lat * 1e7),  # latitude in 1E7
            int(new_long * 1e7),  # longitude in 1E7
            self.current_altitude(),  # altitude (in meters)
            0, 0, 0,  # x, y, z velocity in m/s (not used)
            0, 0, 0,  # x, y, z acceleration (not used)
            0, 0)  # yaw, yaw_rate (not used)

        self.conn.mav.send(msg)
        # self.conn.flush()
        
        
    def move_direction(self, north, east, down):
        """
        Moves the drone in the specified direction.
        """
        print(f"Moving NED for {north}m north, {east}m east, {down}m down")
        self.set_velocity_body(north, east, down)
        

    def adjust_position(self, offset_x, offset_y, sensitivity=0.01):
        move_x = offset_x
        move_y = offset_y 
        print(f"Ajustando posição: move_x: {move_x}, move_y: {move_y}")

        # Envie o comando para o drone
        self.conn.mav.set_position_target_local_ned_send(
            time_boot_ms=0,
            target_system=self.conn.target_system,
            target_component=self.conn.target_component,
            coordinate_frame=mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            type_mask=0b0000111111000111,  # Considera apenas velocidades
            x=0, y=0, z=0,
            vx=move_x, vy=move_y, vz=0,
            afx=0, afy=0, afz=0,
            yaw=0, yaw_rate=0)
    
    def has_reached_position(self, target_lat, target_long):
        """Verifica se o drone chegou à coordenada alvo (com uma margem de erro)."""
        current_lat, current_long, _ = self.get_gps_position()
        distance = self.calculate_distance(current_lat, current_long, target_lat, target_long)
        return distance < 5  # 5 metros

    def move_to_position(self, target_lat, target_long, max_attempts=5, movement_check_interval=5):
        """Move o drone para a posição especificada com verificação de progresso."""
        for attempt in range(max_attempts):
            self.go_to_coord(target_lat, target_long)
            initial_lat, initial_long, _ = self.get_gps_position()
            
            # Verifica se o drone está se movendo em direção à coordenada
            time.sleep(movement_check_interval)
            current_lat, current_long, _ = self.get_gps_position()
            
            if self.is_moving_towards_target(initial_lat, initial_long, current_lat, current_long, target_lat, target_long):
                # Espera até o drone atingir a coordenada
                while not self.has_reached_position(target_lat, target_long):
                    time.sleep(1)
                return True
            else:
                print(f"Tentativa {attempt + 1}/{max_attempts} falhou. Reenviando comando.")
        
        return False
    
    def is_moving_towards_target(self, initial_lat, initial_long, current_lat, current_long, target_lat, target_long):
        """Verifica se o drone está se movendo em direção à coordenada de destino."""
        initial_distance = self.calculate_distance(initial_lat, initial_long, target_lat, target_long)
        current_distance = self.calculate_distance(current_lat, current_long, target_lat, target_long)
        
        # Se a distância atual for menor que a inicial, o drone está se movendo na direção correta
        return current_distance < initial_distance
    
    def calculate_distance(self, lat1, long1, lat2, long2):
        """Calcula a distância entre duas coordenadas usando a fórmula de Haversine."""
        # Converter graus para radianos
        lat1, long1, lat2, long2 = map(math.radians, [lat1, long1, lat2, long2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlong = long2 - long1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlong / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        r = 6371  # Raio da Terra em quilômetros
        return r * c * 1000  # Converter para metros


    def set_home(self, lat, long):
        self.home_lat = lat
        self.home_long = long
    
    def return_to_home(self):
        print("O drone está retornando para HOME")
        self.move_to_position(self.home_lat, self.home_long)
        print("Iniciando pouso")
        self.land()
