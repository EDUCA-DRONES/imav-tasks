# from ultralytics import YOLO
# import cv2
 
# class ZebraModel:
#     def __init__(self, path = 'ml_models/zebra.pt') -> None:
#         self.model = YOLO(path)
    
#     def detect(self, frame):   
#         results = self.model.predict(frame, imgsz=640, conf=0.70, iou=0.45)
#         results = results[0]

#         for i in range(len(results.boxes)):
#             box = results.boxes[i]
#             tensor = box.xyxy[0]
#             x1 = int(tensor[0].item())
#             y1 = int(tensor[1].item())
#             x2 = int(tensor[2].item())
#             y2 = int(tensor[3].item())

#             cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

#             confidence = box.conf[0].item()
#             label = f'{confidence:.2f}'

#             (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
#             cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w, y1), (255, 0, 0), -1)
#             cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
#         return len(results.boxes)
