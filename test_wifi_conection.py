from app.drone.Drone import Drone 
#from moves.DroneMoves import DroneMoveUPFactory

import time
    
def main():  
    # Instantiate the Drone
    drone = Drone()

    # Check if the drone is connected
    if drone.connected():
        print("Drone connected.")
    else:
        print("Failed to connect to the drone.")

    # Define the drone's IP address
    #ip_drone = "192.168.1.100"  # Replace with your drone's actual IP address

    # Continuously check the Wi-Fi connection quality
    while True:
        connection_quality = drone.check_wifi_connection_quality(drone.IP)
        print(f"Connection Quality: {connection_quality}")

        # Wait for a specified period before checking again
        time.sleep(10)  # Check every 10 seconds

main()