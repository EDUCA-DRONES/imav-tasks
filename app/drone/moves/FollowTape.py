import cv2
import numpy as np
from datetime import datetime
import time
from app.drone.Drone import Drone
from app.camera.Camera import Camera
from app.aruco.ArucoDetector import ArucoDetector
from matplotlib import pyplot as plt

class FollowTape:
    def __init__(self, drone: Drone, camera: Camera):
        self.drone = drone
        self.camera = camera
        self.aruco_detector = ArucoDetector()
        self.blue_lower = (100, 150, 0)
        self.blue_upper = (140, 255, 255)
        self.roll_threshold = 50  # Limiar para ajustar o roll
        self.move_forward_distance = 0.5  # Distância para mover para frente
        self.roll_adjustment = 5  # Ajuste do roll

    def follow_tape(self):
        """
        Segue a fita azul detectada no caminho.
        """
        while True:
            self.camera.read_capture()
            frame = self.camera.frame
            mask = self._create_blue_mask(frame)
            largest_contour = self._find_largest_contour(mask)
            #timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # self.camera.save_image(f'imgs/indoor/task1/img-largest_contour_{timestamp}.jpg')
            #cv2.imwrite(f'imgs/indoor/task1/img-largest_contour_{timestamp}.jpg', largest_contour)
            #cv2.imwrite(f'imgs/indoor/task1/img-mask-{timestamp}.jpg', mask)
            
            if largest_contour is not None:
                cX, cY = self._calculate_contour_center(largest_contour)
                error_x = cX - frame.shape[1] // 2
                self._move_forward_and_adjust_roll(error_x)
            else:
                self._adjust_roll_and_move_forward()

            #plt.imshow(cv2.cvtColor(mask, cv2.COLOR_BGR2RGB))
            #plt.axis('off')
            #plt.show()
            #if cv2.waitKey(1) & 0xFF == ord('q'):
                #return
                
            print("\n")
            # Adiciona uma pausa para evitar loop excessivo
            #time.sleep(0.5)

    def _create_blue_mask(self, frame):
        """
        Cria uma máscara para detectar a fita azul.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, self.blue_lower, self.blue_upper)

    def _find_largest_contour(self, mask):
        """
        Encontra o maior contorno na máscara da fita azul.
        """
        print("Encontrando maior contorno da fita azul")
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            return max(contours, key=cv2.contourArea)
            
        return None

    def _calculate_contour_center(self, contour):
        """
        Calcula o centro de um contorno.
        """
        print("Calculando o centro de um contorno")
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cX = int(M['m10'] / M['m00'])
            cY = int(M['m01'] / M['m00'])
            return cX, cY
        return None, None

    def _move_forward_and_adjust_roll(self, error_x):
        """
        Move o drone para frente e ajusta o roll com base no erro na posição do centro do contorno.
        """
        if abs(error_x) > self.roll_threshold:
            print("Ajustando o roll")
            roll_adjustment = self.roll_adjustment if error_x > 0 else -self.roll_adjustment
            print(f"roll_adjustment: {roll_adjustment}")
            self.drone.adjust_roll(roll_adjustment)
        else:
            print(f"Movendo {self.move_forward_distance} m para frente ")
            self.drone.move_forward(self.move_forward_distance)

    def _adjust_roll_and_move_forward(self):
        """
        Ajusta o roll do drone se a fita azul não for detectada e move o drone para frente.
        """
        # Ajusta o roll para tentar alinhar com a fita
        print("Fita azul não detectada. Ajustando o roll.")
        self.drone.adjust_roll(self.roll_adjustment)
        # Move o drone para frente depois de ajustar o roll
        self.drone.move_forward(self.move_forward_distance)
