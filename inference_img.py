import os
from ultralytics import YOLO
import cv2

# Carregando o modelo YOLO
model = YOLO('ml_models/zebra.pt')

# Lendo o frame da imagem
images = []
image_folder = 'imgs/zebra_imgs'
filenames = os.listdir(image_folder)
filenames.sort()
for filename in filenames:
    print(filename)
    img_path = os.path.join(image_folder, filename)
    frame = cv2.imread(img_path)

    # Realizando a predição
    results = model.predict(frame, imgsz=640, conf=0.70, iou=0.45)
    results = results[0]

    # Processando os resultados
    for i in range(len(results.boxes)):
        box = results.boxes[i]
        tensor = box.xyxy[0]
        x1 = int(tensor[0].item())
        y1 = int(tensor[1].item())
        x2 = int(tensor[2].item())
        y2 = int(tensor[3].item())

        # Desenhando a caixa delimitadora
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

        # Obtendo a taxa de confiança
        confidence = box.conf[0].item()
        label = f'{confidence:.2f}'

        # Colocando a taxa de confiança próxima à caixa
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w, y1), (255, 0, 0), -1)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Mostrando o frame processado em tempo real
    cv2.imshow('Video', frame)

    # Aguardar a tecla para fechar a janela
    cv2.waitKey(0)  # Espera indefinidamente até que uma tecla seja pressionada

    # Fechar todas as janelas abertas
    cv2.destroyAllWindows()

    # Se você quiser salvar a imagem processada, descomente a linha abaixo
    # cv2.imwrite('processed_image.jpg', frame)
    print(len(results.boxes))
