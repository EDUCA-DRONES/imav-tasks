import cv2
import cv2.aruco as aruco
#from app.aruco.ArucoCentralizer import ArucoCentralizer

import cv2
print(cv2.__version__)

# Configurações para o detector ArUco
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_5X5_1000)
parameters = aruco.DetectorParameters()


print(cv2.__version__)
# Inicializa a captura de vídeo da câmera
cap = cv2.VideoCapture(0)

while True:
    # Captura um frame do vídeo
    ret, frame = cap.read()
    if not ret:
        print("Falha ao capturar o vídeo.")
        break

    # Converte a imagem para escala de cinza
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detecta os marcadores ArUco
    corners, ids, rejected_img_points = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # Desenha os marcadores detectados
    frame = aruco.drawDetectedMarkers(frame, corners, ids)

    # Exibe o frame com os marcadores detectados
    cv2.imshow('ArUco Detector', frame)
    #aruco_centralizer = ArucoCentralizer()
    #aruco_centralizer.display_video()

    # Imprime os IDs detectados no terminal
    if ids is not None:
        print("IDs detectados:", ids.flatten())
    else:
        print("Nenhum marcador ArUco detectado.")


    # Sai do loop se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a captura e fecha todas as janelas
cap.release()
cv2.destroyAllWindows()
