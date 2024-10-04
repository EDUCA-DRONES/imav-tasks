
from app.drone.Drone import Drone

drone = Drone()

if not drone.connected():
    exit()

drone.change_to_guided_mode()
drone.arm_drone()
drone.ascend(3)

# drone.move_to_position(lat, log)

# drone.adjust_position(0, 5)

# drone.move_south(5)
# drone.move_west(5)
# drone.move_east(5)
# drone.move_north(5)

drone.land()
drone.disarm()


