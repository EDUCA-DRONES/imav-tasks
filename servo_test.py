import cv2
import cv2.aruco as aruco
#from app.aruco.ArucoCentralizer import ArucoCentralizer
from app.drone.Drone import Drone
from app.servo.ServoController import ServoController

def main():
    try:
        drone = Drone()

        try:
            print("Tentando conectar com o drone")
            if not drone.connected():
                print("Falha ao conectar com o drone.")
                return
            print("Crianvo obj ServoController")
            servo = ServoController(drone)

            print("Utilizando activate-servo()")
            #servo_controller.activate_servo(180)
            servo.release_trap()
            #servo.activate_servo(180)
        
        except KeyboardInterrupt as e:
            print(e)
        
        #servo_controller = ServoController('/dev/serial/by-id/usb-ArduPilot_Pixhawk1-1M_3E0039001651343037373231-if00')  # Substitua pelo seu endereço de conexão
        # angle = 90
        # servo_controller.set_servo_angle(angle)

        # pwm_value = 1500
        # servo_controller.set_servo_pwm(pwm_value)

        # angle_from_pwm = servo_controller.pwm_to_angle(pwm_value)
        # print(f"Ângulo correspondente ao PWM {pwm_value}: {angle_from_pwm} graus")


        

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()