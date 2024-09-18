from datetime import datetime
import os
import cv2
import piexif
from PIL import Image
from fractions import Fraction

class FileManager:
    def __init__(self, save_path: str, meta_path: str) -> None:
        self.save_path = save_path
        self.meta_path = meta_path
        self.type_img_dir = ''
        self.type_meta_dir = ''
        self.timestamp = None
        
    def create_base_dirs(self) -> None:
        """Cria os diretórios base para salvar imagens e metadados."""
        os.makedirs(self.save_path, exist_ok=True)
        os.makedirs(self.meta_path, exist_ok=True)
        
    def create_type_dir(self, type: str, alt: float) -> None:
        """Cria diretórios específicos para um tipo de imagem e altitude."""
        self.type_img_dir = os.path.join(self.save_path, type, f'alt_{alt}')
        self.type_meta_dir = os.path.join(self.meta_path, type, f'alt_{alt}')
        os.makedirs(self.type_img_dir, exist_ok=True)
        os.makedirs(self.type_meta_dir, exist_ok=True)
    
    def create_image(self, frame: any, alt: float, index: int) -> None:
        """Salva uma imagem com um timestamp único e adiciona metadados EXIF."""
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        image_filename = os.path.join(self.type_img_dir, f'alt_{alt}_Image_{index+1}_{self.timestamp}.jpg')
        cv2.imwrite(image_filename, frame)
        
        print(f"Imagem {index+1} capturada e salva em: {image_filename}")
        
    def create_meta_data(self, lat: float, long: float, alt: float, real_alt: float, index: int, timestamp: str = None, quantity_zebra: int = 0, img_name: str = '') -> None:
        """Cria um arquivo de metadados e adiciona metadados EXIF à imagem JPEG."""
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        metadata_filename = os.path.join(self.meta_path, f"{index}-{timestamp or self.timestamp}-zebra-{'yes' if quantity_zebra > 0 else 'not'}.txt")
        try:
            with open(metadata_filename, 'w') as metafile:
                metafile.write(f"Timestamp: {self.timestamp}\n")
                metafile.write(f"Latitude: {lat}\n")
                metafile.write(f"Longitude: {long}\n")
                metafile.write(f"Altitude: {real_alt}m\n")
                metafile.write(f'Zebra Quantity: {quantity_zebra}\n')
        except IOError as e:
            print(f"Erro ao criar o arquivo de metadados: {e}")
        
    def add_exif_data(self, image_path: str, lat: float, long: float, alt: float, timestamp: str) -> None:
        """Adiciona metadados EXIF à imagem JPEG usando a biblioteca piexif."""
        try:
            # Carregar EXIF existente ou criar um novo dicionário EXIF
            exif_dict = piexif.load(image_path)
        
            # Atualizar EXIF com novos dados
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = f"Altitude: {alt}m".encode('utf-8')
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = timestamp.encode('utf-8')

            # Função para converter graus decimais para formato de racionais (numerador, denominador)
            def to_rational(value):
                """Converte um valor em graus decimais para uma tupla de racionais (numerador, denominador)."""
                fraction = Fraction(value).limit_denominator(10000)
                return (fraction.numerator, fraction.denominator)

            # Função para converter graus decimais para graus, minutos e segundos
            def degrees_to_dms(value):
                """Converte um valor de graus decimais em graus, minutos e segundos."""
                sign = 'N' if value >= 0 else 'S'
                abs_value = abs(value)
                degrees = int(abs_value)
                minutes = int((abs_value - degrees) * 60)
                seconds = round((abs_value - degrees - minutes / 60) * 3600, 5)
                return (degrees, minutes, seconds, sign)

            def convert_dms_to_rational(dms):
                """Converte graus, minutos e segundos para formato de racionais para EXIF."""
                return [to_rational(dms[0]), to_rational(dms[1]), to_rational(dms[2])]

            lat_dms = degrees_to_dms(lat)
            lon_dms = degrees_to_dms(long)

            exif_dict['GPS'] = {
                piexif.GPSIFD.GPSLatitudeRef: lat_dms[3].encode('utf-8'),
                piexif.GPSIFD.GPSLongitudeRef: lon_dms[3].encode('utf-8'),
                piexif.GPSIFD.GPSLatitude: convert_dms_to_rational(lat_dms),
                piexif.GPSIFD.GPSLongitude: convert_dms_to_rational(lon_dms),
                piexif.GPSIFD.GPSAltitude: to_rational(alt),
                piexif.GPSIFD.GPSAltitudeRef: '0'  # 0 significa acima do nível do mar
            }

            # Converter EXIF dict para bytes
            exif_bytes = piexif.dump(exif_dict)
                
            # Atualizar EXIF na imagem
            img = Image.open(image_path)
            img.save(image_path, exif=exif_bytes)
            
            print(f"Metadados EXIF adicionados à imagem: {image_path}")
        except OverflowError as e:
            print(f"Erro de overflow ao adicionar EXIF: {e}")
        except Exception as e:
            print(f"Erro inesperado: {e}")
