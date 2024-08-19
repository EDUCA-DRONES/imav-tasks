from datetime import datetime
import os
import cv2

class FileManager:
    def __init__(self) -> None:
        self.save_path = 'captured_images_tests_4'
        self.meta_path = 'metadata_images_tests_4'
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
        
    def create_meta_data(self, lat, long, alt, real_alt, index):
        metadata_filename = f"{self.type_meta_dir}/alt_{alt}_Metadata_{index+1}_{self.timestamp}.txt"
        with open(metadata_filename, 'w') as metafile:
            metafile.write(f"Timestamp: {self.timestamp}\n")
            metafile.write(f"Latitude: {lat}\n")
            metafile.write(f"Longitude: {long}\n")
            metafile.write(f"Altitude: {real_alt}m\n")