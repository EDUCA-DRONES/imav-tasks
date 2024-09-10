import cv2
import cv2.aruco as aruco
from app.drone.Drone import Drone

NORTH_ID = 10
SOUTH_ID = 27
EAST_ID = 65
WEST_ID = 48

class ArucoDetector:
    def __init__(self) -> None:
        self.ids = []
        self.corners = []
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
        self.aruco_params = aruco.DetectorParameters()
        self.aruco_size = 0.10

     
    def detect_arucos(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
        
        aruco_params = aruco.DetectorParameters()
        corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)
        self.ids, self.corners = ids, corners if ids is not None else (None, None)

        if self.ids is not None:
            image = aruco.drawDetectedMarkers(image, corners, ids)

        return image, ids, corners
    
    def go_to_aruco_direction(self, drone: Drone, distance_m = 0.5):
        
        print(self.ids)
        if self.ids:
            print('Realizando movimento para direção')
            if NORTH_ID in self.ids:
                drone.move_north(distance_m)
            elif SOUTH_ID in self.ids:
                drone.move_south(distance_m)
            elif EAST_ID in self.ids:
                drone.move_east(distance_m)
            elif WEST_ID in self.ids:
                drone.move_west(distance_m)
            # else:
            self.ids = []
            
            # time.sleep(1)
    
    def get_aruco_positions(self, frame, camera_matrix, dist_coeffs):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
        corners, ids, rejected = self.detect_arucos_base(gray)
        
        if ids is not None:
            # Estimate pose of each marker
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, self.aruco_size, camera_matrix, dist_coeffs)  # 0.15 is the marker length in meters
            
            for i in range(len(ids)):
                # Draw axis and marker
                cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], 0.1)
                cv2.aruco.drawDetectedMarkers(frame, corners)
                
                # Send landing message to drone
                x, y, z = tvecs[i][0][0], tvecs[i][0][1], tvecs[i][0][2]
                #send_land_message(x, y)
                print(f"Marker ID: {ids[i]}, Position: {tvecs[i]}")
                return {
                    'x': x,
                    'y': y,
                    'z': z
                }
            
        return None