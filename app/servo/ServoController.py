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
        self.min_pwm = 1000  # PWM mínimo (normalmente 1ms)
        self.max_pwm = 2000  # PWM máximo (normalmente 2ms)
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
        Define o ângulo do servo motor convertendo para PWM e enviando o comando.
        
        :param angle: Ângulo desejado em graus
        """
        pwm_value = self.angle_to_pwm(angle)
        print(f"Convertendo ângulo {angle} graus para PWM {pwm_value}")
        #print(f"PWM correspondente ao ângulo: {angle} graus: PWM {pwm_value}")
        self.set_servo_pwm(pwm_value)
        print(f"Ângulo do servo configurado para {angle} graus")

    def activate_servo(self, angle):
        try:
            print("Acionando o servo...")
            pwm_value = self.angle_to_pwm(angle)
            print(f"PWM correspondente ao ângulo: {angle} graus: PWM {pwm_value}")

            
            if pwm_value == 2000:
                print("O servo está girando no sentido horário")
            elif pwm_value == 1000:
                print("O servo está girando no sentido anti-horário")


            self.conn.mav.command_long_send(
                self.conn.target_system,
                self.conn.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                0,  # confirmation
                self.servo_channel,  # Canal do servo
                pwm_value,  # PWM para ativar o servo (ajuste conforme necessário)
                0, 0, 0, 0, 0, 0
            )

            if pwm_value == 1500:
                print("O servo parou de se mover")
                #print("Servo acionado.")
            
        
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    def release_trap(self):
        """
        Aciona o mecanismo de liberação da armadilha.
        """
        try:
            
            self.activate_servo(180)

            time.sleep(15)
            print("Armadilha liberada com sucesso.")

            self.activate_servo(90)

        except Exception as e:
            print(f"Erro ao liberar a armadilha: {e}")
  

if __name__ == "__main__":
   
    try:
        drone = Drone()
        #servo_controller = ServoController('/dev/serial/by-id/usb-ArduPilot_Pixhawk1-1M_3E0039001651343037373231-if00')  # Substitua pelo seu endereço de conexão
        # angle = 90
        # servo_controller.set_servo_angle(angle)

        # pwm_value = 1500
        # servo_controller.set_servo_pwm(pwm_value)

        # angle_from_pwm = servo_controller.pwm_to_angle(pwm_value)
        # print(f"Ângulo correspondente ao PWM {pwm_value}: {angle_from_pwm} graus")


        print("Utilizando activate-servo()")
        #servo_controller.activate_servo(180)
        servo_controller.release_trap()

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
