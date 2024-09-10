import threading
import time

class DroneController:
    def __init__(self):
        self.current_altitude_value = 0.0
        self.altitude_thread_running = True
        self.altitude_thread = threading.Thread(target=self.update_altitude)
        self.altitude_thread.start()

    def update_altitude(self):
        while self.altitude_thread_running:
            msg = self.conn.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
            if msg:
                self.current_altitude_value = msg.relative_alt / self.METER_CONVERTER
            time.sleep(0.1)  # Atualiza a cada 100ms (ajuste conforme necessário)

    def get_current_altitude(self):
        return self.current_altitude_value

    def stop_altitude_thread(self):
        self.altitude_thread_running = False
        self.altitude_thread.join()
