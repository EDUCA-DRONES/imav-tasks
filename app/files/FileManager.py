from datetime import datetime
import os
import cv2

class FileManager:
    def __init__(self, save_path, meta_path) -> None:
        self.save_path = save_path
        self.meta_path =  meta_path
        self.type_img_dir = ''
        self.type_meta_dir = ''
        self.timestamp = None
        
    def create_base_dirs(self):
        os.makedirs(self.save_path, exist_ok=True)
        os.makedirs(self.meta_path, exist_ok=True)
        
    def create_type_dir(self, type, alt):
        self.type_img_dir = f'{self.save_path}/{type}/alt_{alt}'
        self.type_meta_dir = f'{self.meta_path}/{type}/alt_{alt}'
        os.makedirs(self.type_img_dir, exist_ok=True)
        os.makedirs(self.type_meta_dir, exist_ok=True)
    
    def create_image(self, frame, alt, index):
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        image_filename = f"{self.type_img_dir}/alt_{alt}_Image_{index+1}_{self.timestamp}.jpg"
        cv2.imwrite(image_filename, frame)
        print(f"Imagem {index+1} capturada e salva em: {image_filename}")
        
    def create_meta_data(self, lat, long, alt, real_alt, index, timestamp=None, quantity_zebra=0):
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        metadata_filename = f"{self.meta_path}/{index}-{timestamp}-zebra-{'yes' if quantity_zebra > 0 else 'not'}.txt"
        with open(metadata_filename, 'w') as metafile:
            metafile.write(f"Timestamp: {self.timestamp}\n")
            metafile.write(f"Latitude: {lat}\n")
            metafile.write(f"Longitude: {long}\n")
            metafile.write(f"Altitude: {real_alt}m\n")
            metafile.write(f'Zebra Quantitity: {quantity_zebra}')