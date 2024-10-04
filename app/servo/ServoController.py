from pymavlink import mavutil
from app.drone.Drone import Drone
import time

class ServoController:
    def __init__(self, drone: Drone, servo_channel=7):

        """
        Inicializa a conexão com a Pixhawk e configura o canal do servo.
        
        :param connection_string: String de conexão MAVLink, por exemplo, 'udp:127.0.0.1:14550'
        :param servo_channel: Canal do servo na Pixhawk
        """
        #self.conn = mavutil.mavlink_connection(connection_string, baud=57600, mav10=False)
        self.conn = drone.conn
        self.servo_channel = servo_channel
        self.min_pwm = 1000  # PWM mínimo para 0 graus
        self.max_pwm = 2000  # PWM máximo para 180 graus
        self.neutral_pwm = 1500  # PWM para 90 graus
        self.angle_range = 180  # Ângulo máximo do servo motor
    
    def set_servo_pwm(self, pwm_value):
        """
        Define o valor PWM do servo motor.
        
        :param pwm_value: Valor PWM a ser enviado ao servo motor (deve estar entre min_pwm e max_pwm)
        """
        if not (self.min_pwm <= pwm_value <= self.max_pwm):
            raise ValueError(f"Valor PWM deve estar entre {self.min_pwm} e {self.max_pwm}")
        
        # Enviando a mensagem SERVO_OUTPUT_RAW com valores para todos os servos
        self.conn.mav.servo_output_raw_send(
            int(self.conn.target_system),  # Sistema alvo (geralmente 1)
            int(self.conn.target_component),  # Componente alvo (geralmente 1)
            int(pwm_value) if self.servo_channel == 1 else 0,  # Canal 1
            0,  # Canal 2
            0,  # Canal 3
            0,  # Canal 4
            0,  # Canal 5
            0,  # Canal 6
            0,  # Canal 7
            0   # Canal 8
        )
        print(f"PWM do servo configurado para {pwm_value}")

    def pwm_to_angle(self, pwm_value):
        """
        Converte o valor PWM para o ângulo correspondente do servo.
        
        :param pwm_value: Valor PWM a ser convertido
        :return: Ângulo correspondente em graus
        """
        angle = (pwm_value - self.min_pwm) / (self.max_pwm - self.min_pwm) * self.angle_range
        return angle

    def angle_to_pwm(self, angle):
        """
        Converte o ângulo para o valor PWM correspondente do servo.
        
        :param angle: Ângulo em graus
        :return: Valor PWM correspondente
        """
        if not (0 <= angle <= self.angle_range):
            raise ValueError(f"Ângulo deve estar entre 0 e {self.angle_range} graus")
        
        pwm_value = self.min_pwm + (angle / self.angle_range) * (self.max_pwm - self.min_pwm)
        return pwm_value

    def set_servo_angle(self, angle):
        """
        Define o ângulo do servo motor convertendo o ângulo para PWM.
        
        :param angle: O ângulo desejado (entre 0° e 180°)
        """
        if angle < 0 or angle > 180:
            raise ValueError("O ângulo deve estar entre 0 e 180 graus.")
        
        # Converte o ângulo para um valor de PWM
        pwm_value = self.min_pwm + int((self.max_pwm - self.min_pwm) * (angle / self.angle_range))
        
        self.conn.mav.command_long_send(
            self.conn.target_system,
            self.conn.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
            0,  # confirmation
            self.servo_channel,  # Canal do servo
            pwm_value,  # PWM para ativar o servo (ajuste conforme necessário)
            0, 0, 0, 0, 0, 0
        )
        # self.conn.mav.servo_output_raw_send(
        #     int(self.conn.target_system),
        #     int(self.conn.target_component),
        #     int(pwm_value) if self.servo_channel == 1 else 0,
        #     0, 0, 0, 0, 0, 0, 0
        # )
        

        print(f"Servo configurado para o ângulo {angle}°, PWM: {pwm_value}")

    def activate_servo(self, angle,  direction='clockwise'):
        """
        Ativa o servo para trabalhar em sentido horário ou anti-horário com base no ângulo.

        :param direction: 'clockwise' para sentido horário, 'counterclockwise' para sentido anti-horário
        :param angle: O ângulo desejado entre 0 e 180 graus
        """
        try:
            if direction == 'clockwise':
                if angle < 90 or angle > 180:
                    raise ValueError("O ângulo para o sentido horário deve estar entre 90° e 180°.")
                print(f"Movendo no sentido horário para {angle} graus.")
                self.set_servo_angle(angle)

            elif direction == 'counterclockwise':
                if angle < 0 or angle > 90:
                    raise ValueError("O ângulo para o sentido anti-horário deve estar entre 0° e 90°.")
                print(f"Movendo no sentido anti-horário para {angle} graus.")
                self.set_servo_angle(angle)

            else:
                raise ValueError("Direção inválida. Use 'clockwise' ou 'counterclockwise'.")

        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def stop_servo(self):
        """
        Função de emergência para parar o servo motor.
        Define o PWM para o valor neutro (geralmente 1500).
        """
        try:
            print("Parando o servo...")

            # Envia o comando para parar o servo
            self.conn.mav.command_long_send(
                self.conn.target_system,
                self.conn.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                0,  # confirmation
                self.servo_channel,  # Canal do servo
                self.neutral_pwm,  # PWM para parar o servo
                0, 0, 0, 0, 0, 0
            )

            print(f"Servo parado com PWM {self.neutral_pwm}")

        except Exception as e:
            print(f"Erro ao tentar parar o servo: {e}")
            
    def release_trap(self):
        """
        Aciona o mecanismo de liberação da armadilha.
        """
        try:
            # Movendo para o sentido horário (enrolando)
            time_activated_servo = 22
            print(f"O servo ficará ativo por {time_activated_servo} segundo(s)")

            # print("Iniciando enrolamento...")
            # self.activate_servo(150, 'clockwise')  # Enrola até 150 graus
            # time.sleep(time_activated_servo)

            # Movendo para o sentido anti-horário (desenrolando)
            print("Iniciando desenrolamento...")
            self.activate_servo(30, 'counterclockwise')  # até 30 graus
            time.sleep(time_activated_servo)

            # Parando o servo
            #self.stop_servo()

        except Exception as e:
            print(f"Erro ao liberar a armadilha: {e}")

        finally:
            self.stop_servo()
            
  

"""if __name__ == "__main__":
   
    try:
        drone = Drone()
        servo = ServoController(Drone)
        #servo_controller = ServoController('/dev/serial/by-id/usb-ArduPilot_Pixhawk1-1M_3E0039001651343037373231-if00')  # Substitua pelo seu endereço de conexão
        # angle = 90
        # servo_controller.set_servo_angle(angle)

        # pwm_value = 1500
        # servo_controller.set_servo_pwm(pwm_value)

        # angle_from_pwm = servo_controller.pwm_to_angle(pwm_value)
        # print(f"Ângulo correspondente ao PWM {pwm_value}: {angle_from_pwm} graus")


        print("Utilizando activate-servo()")
        #servo_controller.activate_servo(180)
        servo.release_trap()

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
"""