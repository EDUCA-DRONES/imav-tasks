import time
from pymavlink import mavutil
from app.drone.moves.DroneMoves import DroneMoveUPFactory
from timeit import default_timer as timer
from app.drone.tools.GPS import GPS
from app.drone.enums.Masks import IGNORE_VELOCITY, POSITION, ONLY_POSITION
from app.drone.DroneController import DroneController


import math
import subprocess
import re

class DroneConfig:
    def __init__(self) -> None:
        self.GUIDED_MODE = 4
        self.x_meters_cover = 12
        self.y_meters_cover = 6
        
# senha:101263
class Drone:
    def __init__(self) -> None:
        self.IP = '127.0.0.1'
        self.PORT = '14551'
        self.PROTOCOL = 'udpin'
        
        # self.IP = '192.168.0.103'
        # self.PORT = '5760'
        # self.PROTOCOL = 'tcp'
        
        # self.URL = f'/dev/serial/by-id/usb-ArduPilot_Pixhawk1-1M_3E0039001651343037373231-if00'

        self.URL = f'{self.PROTOCOL}:{self.IP}:{self.PORT}'
        self.baud = '57600'
        # self.URL = f'/dev/ttyUSB0'
        self.METER_CONVERTER = 1000.0
        self.conn =  mavutil.mavlink_connection(self.URL, baud=self.baud,  mav10=False)
        self.config = DroneConfig()
        self.velocity = 30
        self.gps = GPS()
        #self.servo = ServoController()


        self.home_lat = None
        self.home_long = None

        #self.drone_controller = DroneController()
        
    def connected(self):
        return self.conn.wait_heartbeat(timeout=5)
    
    def solicit_telemetry(self):
        self.conn.mav.request_data_stream_send(self.conn.target_system, self.conn.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
        
    def current_altitude(self):
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
        if msg:
            return msg.relative_alt / self.METER_CONVERTER   # Convertendo de mm para metros
        return None
    
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
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        print(f"msg - msg.lat: {msg.lat} | msg.lon: {msg.lon}")
        if not msg:
            raise Exception("Failed to get current altitude")
            
        # Converta as coordenadas para milésimos de grau
        current_lat = int(msg.lat / 1e7)
        current_lon = int(msg.lon / 1e7)

        # Parâmetros de velocidade (controlando a velocidade de descida)
        velocity_z = 0.5  # Velocidade negativa para descer (em metros por segundo)

        print(f"Descendo para {target_altitude} metros com velocidade {velocity_z} m/s.")
        
        # Enviar comando MAVLink para ajustar altitude e controlar a velocidade
        self.conn.mav.set_position_target_global_int_send(
            0,  # time_boot_ms (não usado)
            self.conn.target_system, self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Altitude relativa ao terreno
            0b0000111111000111,  # Ignora outras componentes (somente latitude, longitude, altitude e velocidade Z)
            current_lat,  # Latitude atual (mantida)
            current_lon,  # Longitude atual (mantida)
            int(target_altitude),  # Altitude desejada em milímetros
            0, 0, velocity_z,  # Componentes de velocidade (X, Y, Z). Somente Z é usado.
            0, 0, 0,  # Componentes de aceleração (ignorado)
            0, 0  # Yaw, yaw_rate (ignorado)
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

    def go_to_coord(self, new_lat, new_long, alt_return=15):
      
        # Enviar comando para ir para a nova coordenada
        msg = mavutil.mavlink.MAVLink_set_position_target_global_int_message(
            0,  # time_boot_ms (not used)
            0, 0,  # target system, target component
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            0b0000111111111000,  # type_mask (only positions enabled)
            int(new_lat * 1e7),  # latitude in 1E7
            int(new_long * 1e7),  # longitude in 1E7
            int(alt_return),  # altitude (in meters)
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

    def move_to_position(self, target_lat, target_long, max_attempts=20, movement_check_interval=5):
        """Move o drone para a posição especificada com verificação de progresso e otimizações."""
        attempt = 0
        
        while attempt < max_attempts:
            # Envia comando para mover o drone
            self.go_to_coord(target_lat, target_long)
            initial_lat, initial_long, _ = self.get_gps_position()
            
            while True:
                # Aguarda um curto período antes de verificar o progresso
                time.sleep(movement_check_interval)
                current_lat, current_long, _ = self.get_gps_position()
                
                # Verifica se o drone está se movendo na direção correta
                if self.is_moving_towards_target(initial_lat, initial_long, current_lat, current_long, target_lat, target_long):
                    # Verifica se o drone atingiu a coordenada
                    if self.has_reached_position(target_lat, target_long):
                        print(f"Posição {target_lat}, {target_long} alcançada com sucesso.")
                        return True
                    break  # Sai do loop de verificação e tenta novamente se necessário
                else:
                    print(f"Tentativa {attempt + 1}/{max_attempts} falhou. Reenviando comando.")
                    attempt += 1
                    if attempt >= max_attempts:
                        print("Número máximo de tentativas alcançado. Falha ao mover para a posição.")
                        return False
                    # Envia um novo comando para tentar mover o drone novamente
                    self.go_to_coord(target_lat, target_long)
        
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
        # Verifica se as coordenadas de HOME estão definidas
        if self.home_lat is None or self.home_long is None:
            raise ValueError("Coordenadas de retorno para HOME não foram definidas.")
    

        print(f"O drone está retornando para HOME: Lat {self.home_lat}, Lon {self.home_long}")
        self.move_to_position(self.home_lat, self.home_long)
        print("Iniciando pouso")
        self.land()
        self.disarm() 
 
    def wait_until_altitude_reached(self, target_altitude: float, tolerance: float = 0.5, timeout: float = 120.0, resend_interval: float = 5.0) -> bool:
        """
        Espera até que o drone atinja a altitude desejada, com uma tolerância opcional.
        
        Parâmetros:
        - target_altitude: Altitude que o drone deve alcançar.
        - tolerance: Variação permitida entre a altitude atual e a desejada (padrão: 0.2 metros).
        - timeout: Tempo máximo de espera em segundos (padrão: 15 segundos).
        
        Retorna:
        - True se o drone alcançar a altitude desejada dentro do tempo limite.
        - False se o tempo limite for atingido e o drone não alcançar a altitude desejada.
        """
        start_time = time.time()
        last_command_time = start_time
        
        #print(f"Altitude inicial: {initial_altitude} metros")

        while time.time() - start_time < timeout:
            initial_altitude = self.current_altitude()

            print(f"Altitude atual: {self.current_altitude()} metros, aguardando atingir {target_altitude} metros...")

            self.check_safe_altitude(min_altitude=1.0, safe_altitude=1.5)

            # if abs(self.current_altitude()) <= target_altitude and abs(self.current_altitude()) >= (target_altitude * 0.8):
            if abs(self.current_altitude() - target_altitude) <= tolerance:
                print(f"Altitude atingida: {self.current_altitude()} metros (dentro da tolerância de {tolerance} metros)")
                return True
            
            # Verifique se o drone está descendo
            altitude_difference = initial_altitude - self.current_altitude()
            print(f"Altitude inicial: {initial_altitude}, Altitude atual: {self.current_altitude()}, Diferença: {altitude_difference}")
            if altitude_difference < 1.0:  # Se a diferença for menor que 1 metro
                if time.time() - last_command_time >= resend_interval:
                    print(f"Drone não está descendo como esperado. Reenviando comando para ajustar altitude para {target_altitude} metros.")
                    self.descend(target_altitude)  # Envie o comando para ajustar a altitude novamente
                    last_command_time = time.time()
                    initial_altitude = self.current_altitude()  # Atualize a altitude inicial para a nova altitude atual
                #time.sleep(5)

            

            # Verifica se é hora de reenviar o comando
            # if time.time() - last_command_time >= resend_interval:
            #     print(f"Reenviando comando para ajustar altitude para {target_altitude} metros.")
            #     self.descend(target_altitude)  # Envie o comando para ajustar a altitude novamente
            #     last_command_time = time.time()

            time.sleep(1)  # Aguardar 1 segundo antes de verificar novamente
            if start_time == 100:
                print(f"Passaram-se {start_time} segundos")
        
        print(f"Falha ao atingir a altitude desejada de {target_altitude} metros dentro do tempo limite.")
        return False

    def check_wifi_connection_quality(self, ip_drone, attempts=4, timeout=1):
        """
        Checks the Wi-Fi connection quality to the drone and evaluates the connection strength.

        Parameters:
        - ip_drone (str): The drone's IP address.
        - attempts (int): Number of ping packets to send. Default is 4.
        - timeout (int): Timeout for each ping response in seconds. Default is 1 second.

        Returns:
        - str: 'Strong Connection', 'Moderate Connection', 'Weak Connection', or 'No Connection'.
        """
        try:
            # Construct the ping command
            ping_command = ['ping', '-c', str(attempts), '-W', str(timeout), ip_drone]

            # Execute the ping command
            response = subprocess.run(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the ping command was successful
            if response.returncode != 0:
                print(f"Drone unreachable at {ip_drone}. Check the Wi-Fi connection.")
                return "No Connection"

            # Analyze the output to extract the average response time (latency)
            output = response.stdout.decode()
            
            # Use a regular expression to capture the average ping time
            match = re.search(r"min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms", output)

            if match:
                average_latency = float(match.group(1))
                print(f"Average latency: {average_latency} ms")

                # Evaluate the connection quality based on average latency
                if average_latency < 50:
                    return "Strong Connection"
                elif 50 <= average_latency <= 150:
                    return "Moderate Connection"
                else:
                    return "Weak Connection"
            else:
                print("Unable to obtain average latency.")
                return "No Connection"

        except Exception as e:
            print(f"Error checking connection: {e}")
            return "No Connection"
        
    # Função auxiliar para converter roll, pitch, yaw em quatérnions
    def euler_to_quaternion(self, roll, pitch, yaw):
        """
        Converte ângulos de Euler (roll, pitch, yaw) para quatérnions.
        """
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        
        return [qw, qx, qy, qz]

    def send_attitude_control(self, roll, pitch, yaw, thrust):
        """
        Envia um comando de controle de atitude ao drone.
        """
        # Converte ângulos de Euler (roll, pitch, yaw) em quatérnions
        quat = self.euler_to_quaternion(roll, pitch, yaw)
        
        # Envia o comando de atitude usando o MAVLink
        self.conn.mav.set_attitude_target_send(
            0,  # Tempo de envio (0 para enviar imediatamente)
            self.conn.target_system,  # ID do sistema do alvo
            self.conn.target_component,  # ID do componente do alvo
            0b00000000,  # Flags de controle (usa ângulos de Euler em vez de quatérnions)
            quat,  # Quatérnions calculados a partir de roll, pitch, yaw
            0, 0, 0,  # Velocidade angular (pode ser deixada como 0)
            thrust  # Empuxo (normalizado entre 0 e 1)
        )
               
    def rotate_yaw(self, yaw_angle_deg):
        # Gira o drone no eixo yaw em graus
        yaw_rate = yaw_angle_deg * (3.14159 / 180)  # Converte graus para radianos
        duration = 2  # Tempo em segundos (ajuste conforme necessário)
        self.send_movement_command(vx=0, vy=0, vz=1.5, yaw_rate=yaw_rate, duration=duration)


    def adjust_roll(self, angle_degrees, duration=5):
        """
        Ajusta o roll do drone por um ângulo específico.
        """
        # Converte o ângulo de graus para radianos
        angle_radians = angle_degrees * (math.pi / 180.0)
        
        # Obtém a orientação atual
        attitude = self.conn.recv_match(type='ATTITUDE', blocking=True)
        current_roll = attitude.roll
        
        # Define o novo roll baseado no ajuste desejado
        target_roll = current_roll + angle_radians
        
        # Envia o comando de ajuste
        start_time = time.time()
        while time.time() - start_time < duration:
            # Ajuste o comando conforme necessário para sua aplicação
            self.send_attitude_control(target_roll, 0, 0, 1)  # Roll é ajustado, pitch e yaw são 0, thrust é ajustável
            time.sleep(1)  # Espera 1 segundo antes de enviar o próximo comando

    def send_movement_command(self, vx, vy, vz, yaw_rate, duration):
        # Envia comando de movimento com velocidade em m/s e taxa de yaw
        print("Movendo o drone...")
        for _ in range(duration):
            self.conn.mav.set_position_target_local_ned_send(
                0,
                self.conn.target_system,
                self.conn.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                int(0b110111111000),  # Controla posição e yaw
                0, 0, 0,  # Não altera posição (apenas velocidade)
                vx, vy, vz,  # Velocidade nos eixos x, y, z
                0, 0, 0,  # Acelerações (não são usadas aqui)
                yaw_rate,  # Taxa de rotação no yaw (rad/s)
                0  # Yaw rate
            )
            time.sleep(1)

    def move_forward(self, distance_meters, speed_mps):
        # Move o drone para frente uma distância específica
        duration = int(distance_meters / speed_mps)
        self.send_movement_command(vx=speed_mps, vy=0, vz=0, yaw_rate=0, duration=duration)


    def check_and_adjust_altitude(self, desired_altitude):
        """
        Verifica a altitude atual e ajusta se necessário.
        """
        current_altitude = self.current_altitude()
        if abs(current_altitude - desired_altitude) > 0.1:  # Tolera uma pequena variação
            print(f"Ajustando altitude para {desired_altitude} metros.")
            self.set_altitude(desired_altitude)

    def check_safe_altitude(self, min_altitude: float = 1.0, safe_altitude: float = 1.5):
        """
        Verifica se o drone está abaixo da altitude mínima permitida e o corrige se necessário.
        
        Parâmetros:
        - min_altitude: A altitude mínima permitida para o drone (padrão: 0.5 metros).
        - safe_altitude: A altitude para a qual o drone deve subir caso esteja abaixo do mínimo (padrão: 1.0 metros).
        """
        print("Verificando altitude segura do drone")
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        
        if not msg:
            raise Exception("Falha ao obter a altitude atual do drone.")
        
        current_altitude = msg.relative_alt / 1000
        print(f"Para segurança. Altitude atual do drone: {current_altitude} metros\n\n")

        # Verificação da altitude mínima
        if current_altitude < min_altitude:
            print(f"Altitude abaixo do limite mínimo de {min_altitude} metros. Subindo para {safe_altitude} metros.")

            # Enviar comando MAVLink para subir à altitude segura
            current_lat = int(msg.lat * 1e7)
            current_lon = int(msg.lon * 1e7)

            # Enviar comando para ajustar a altitude para a altitude segura (safe_altitude)
            self.conn.mav.set_position_target_global_int_send(
                0,  # time_boot_ms (não usado)
                self.conn.target_system, self.conn.target_component,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Altitude relativa ao terreno
                0b0000111111000111,  # Ignora outras componentes
                current_lat,  # Latitude atual (mantida)
                current_lon,  # Longitude atual (mantida)
                int(safe_altitude),  # Altitude desejada em milímetros
                0, 0, 0,  # Componentes de velocidade (ignorado)
                0, 0, 0,  # Componentes de aceleração (ignorado)
                0, 0  # Yaw, yaw_rate (ignorado)
            )
            
            print(f"Comando enviado para subir para {safe_altitude} metros.")
            time.sleep(5)
            if self.current_altitude() >= min_altitude:
                print("Altitude segura alcançada")
        else:
            print("Altitude dentro dos limites permitidos.")