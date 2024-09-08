
from ultralytics import YOLO
import cv2

# Carregando um modelo personalizado
print('test')
model = YOLO('ml_models/zebra.pt')
print('test')
 
# Lendo o vídeo
cap = cv2.VideoCapture(0)
print('test')

# Verificando se o vídeo foi aberto corretamente
if not cap.isOpened():
    print("Erro ao abrir o vídeo.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

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

    # Parando a visualização quando a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberando o vídeo e fechando todas as janelas abertas

cap.release()
cv2.destroyAllWindows()