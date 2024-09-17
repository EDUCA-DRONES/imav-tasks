import matplotlib.pyplot as plt
import os
import csv
import os
from datetime import datetime

import pytz

# os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

class MetaSingleton:
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class DetectionsByAltReport(MetaSingleton):

    initial_state = {
        'rtsp': 0,
        'computer': 0,
        'imx': 0,
        'analog': 0,
        'esp32': 0
    }
    
    data = {
        '3': initial_state.copy(),
        '6': initial_state.copy(),
        '9': initial_state.copy(),
        '12': initial_state.copy(),
        '15': initial_state.copy()
    }
    
    def save_data(self, _type, alt, detections):
        self.data[str(alt)][_type] += detections
    
    def generate_and_save_plots(self, folder_path):
        print(self.data)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        csv_file_path = os.path.join(folder_path, 'data_summary.csv')
        
        with open(csv_file_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Alt', 'Type', 'Detected ArUcos'])  # Header
            
            for alt, values in self.data.items():
                types = list(values.keys())
                counts = list(values.values())
                
                for type_, count in zip(types, counts):
                    csv_writer.writerow([alt, type_, count])
                
                plt.figure()
                plt.bar(types, counts)
                plt.xlabel('Type')
                plt.ylabel('Detected ArUcos')
                plt.title(f'Captured Images at Altitude {alt}')
                
                file_path = os.path.join(folder_path, f'alt_{alt}.png')
                plt.savefig(file_path)
                plt.close()
                
class FlightLogger:
    def __init__(self, log_file='flight_log.csv'):
        self.log_file = log_file
        self.initialize_log_file()

    def initialize_log_file(self):
        # Cria o arquivo CSV e escreve o cabeçalho
        with open(self.log_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time UTC', 'Latitude', 'Longitude', 'Altitude', 'Current', 'Voltage'])

    def log_position(self, zebra_id, image_id, lat, long, alt, image_name):
        # Registra a posição atual do drone no arquivo CSV
        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            timestamp = datetime.utcnow().isoformat()  # Hora UTC no formato AAAA-MM-DDTHH:MM:SS.sss
            writer.writerow([zebra_id, image_id, timestamp, lat, long, alt, image_name])

    def log_performance(self, lat, long, alt, voltage, current):
        with open(self.log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            tz = pytz.timezone('Europe/London')
            time_now = datetime.now(tz)
            timestamp = time_now.isoformat()  # Time in ISO format
            writer.writerow([ timestamp, lat, long, alt, voltage, current])

# Example usage:
# singleton = ReportCapturedImagesSingleton()
# singleton.generate_and_save_plots('path_to_your_folder')
