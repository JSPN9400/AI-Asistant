from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        # Expect the user to download the YOLO model to the project root.
        self.model = YOLO(model_path)

    def detect(self, frame) -> list[str]:
        results = self.model(frame, verbose=False)
        names = self.model.names
        labels: list[str] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.item())
                labels.append(names[cls_id])
        # Return unique labels preserving order
        seen = set()
        unique_labels: list[str] = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)
        return unique_labels

