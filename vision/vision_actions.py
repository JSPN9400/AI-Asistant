_camera = None
_detector = None


def _ensure():
    global _camera, _detector
    if _camera is None:
        from .camera import Camera

        _camera = Camera()
    if _detector is None:
        from .object_detection import ObjectDetector

        _detector = ObjectDetector()
    return _camera, _detector


def describe_scene() -> str:
    cam, det = _ensure()
    frame = cam.capture_frame()
    labels = det.detect(frame)
    if not labels:
        return "I don't see any recognizable objects."
    return "I can see: " + ", ".join(labels)

