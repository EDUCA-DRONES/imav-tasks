from abc import ABC, abstractmethod
from pymavlink import mavutil

from app.drone.enums.Masks import IGNORE_VELOCITY

class DroneMoveUP(ABC):
    def __init__(self, conn) -> None:
        super().__init__()
        self.conn = conn
        
    @abstractmethod
    def execute(self, target_altitude, ascent_speed=1.0):
        raise Exception('Method not implemented')
    
class DroneTakeOff(DroneMoveUP):
    def execute(self, target_altitude, ascent_speed=1.0):
        # Determine the type of autopilot and adjust the takeoff command accordingly
        msg = self.conn.recv_match(type='HEARTBEAT', blocking=True)
        if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
            print("Connected to ArduPilot autopilot")
            mode_id = self.conn.mode_mapping()["GUIDED"]
            takeoff_params = [0, 0, 0, 0, 0, 0, target_altitude]
        elif msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_PX4:
            print("Connected to PX4 autopilot")
            mode_id = self.conn.mode_mapping()["TAKEOFF"][1]
            start_msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
            starting_alt = start_msg.alt / 1000
            takeoff_params = [0, 0, 0, 0, float("NAN"), float("NAN"), starting_alt + target_altitude]
        else:
            raise ValueError("Autopilot not supported")

        # Change mode to guided (Ardupilot) or takeoff (PX4)
        self.conn.mav.command_long_send(
            self.conn.target_system, 
            self.conn.target_component, 
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id, 0, 0, 0, 0, 0
        )
        ack_msg = self.conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        print(f"Change Mode ACK:  {ack_msg}")

        # Arm the UAS
        self.conn.mav.command_long_send(
            self.conn.target_system, 
            self.conn.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 
            0, 1, 0, 0, 0, 0, 0, 0
        )

        arm_msg = self.conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        print(f"Arm ACK:  {arm_msg}")

        # Command Takeoff
        print(f"Decolando para altitude de {target_altitude} metros com velocidade de {ascent_speed} m/s...")
        self.conn.mav.command_long_send(
            self.conn.target_system, 
            self.conn.target_component, 
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 
            0, takeoff_params[0], takeoff_params[1], takeoff_params[2], takeoff_params[3], takeoff_params[4], takeoff_params[5], takeoff_params[6]
        )

        takeoff_msg = self.conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        print(f"Takeoff ACK:  {takeoff_msg}")

        return takeoff_msg.result

class DroneChangeAlt(DroneMoveUP):
    def execute(self, target_altitude, ascent_speed=8.0):
        print(f"Subindo para {target_altitude} metros com velocidade de {ascent_speed} m/s...")

        # Get the current altitude from the drone
        msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if not msg:
            raise Exception("Failed to get current altitude")

        # Send the MAVLink command to change the altitude
        self.conn.mav.set_position_target_global_int_send(
            0,  # time_boot_ms (not used)
            self.conn.target_system, self.conn.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Altitude relative to the terrain
            IGNORE_VELOCITY,  # Type mask (ignore velocities)
            int(msg.lat),  # Latitude (unchanged)
            int(msg.lon),  # Longitude (unchanged)
            int(target_altitude),  # Desired altitude in millimeters
            0, 0, 0,  # Velocity components (ignored)
            0, 0, 0,  # Acceleration components (ignored)
            0, 0)  # Yaw, yaw_rate (ignored)

class DroneMoveUPFactory:
    @staticmethod
    def create(current_alt, conn) -> DroneMoveUP: 
        type = 'takeoff' if current_alt < 1 else 'change_alt'
        
        moves = {
            'takeoff' : DroneTakeOff,
            'change_alt': DroneChangeAlt,
        }
           
        return moves[type](conn)