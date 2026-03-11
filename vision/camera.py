import cv2


class Camera:
    def __init__(self, index: int = 0):
        self.cap = cv2.VideoCapture(index)

    def capture_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Failed to capture frame from webcam")
        return frame

    def release(self) -> None:
        self.cap.release()

