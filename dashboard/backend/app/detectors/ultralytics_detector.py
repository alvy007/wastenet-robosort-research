from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from .base import BaseDetector

CLASS_NAMES = {
    0: "electronic",
    1: "glass",
    2: "metal",
    3: "others",
    4: "paper",
    5: "plastic",
}


class UltralyticsDetector(BaseDetector):
    def __init__(
        self,
        model_path: Path,
        model_id: str,
        model_label: str,
        image_size: int = 640,
        conf: float = 0.10,
        device: str = "auto",
    ) -> None:
        self.model_path = Path(model_path)
        self.model_id = model_id
        self.model_label = model_label
        self.image_size = image_size
        self.conf = conf
        self.device = device
        self.model = None
        self.load_error: str | None = None
        self._lock = threading.Lock()

    def load(self) -> None:
        if self.model is not None:
            return
        if not self.model_path.exists():
            self.load_error = f"Model file not found: {self.model_path}"
            return

        try:
            from ultralytics import YOLO

            self.model = YOLO(str(self.model_path))
            self.load_error = None
        except Exception as exc:  # app should stay available even if the weight cannot load
            self.model = None
            self.load_error = f"{type(exc).__name__}: {exc}"

    def status(self) -> dict[str, Any]:
        return {
            "id": self.model_id,
            "label": self.model_label,
            "family": "Ultralytics YOLO",
            "loaded": self.model is not None,
            "model_path": str(self.model_path),
            "model_exists": self.model_path.exists(),
            "load_error": self.load_error,
            "image_size": self.image_size,
            "internal_confidence_threshold": self.conf,
            "device": self.device,
        }

    def predict(self, image_bgr: np.ndarray) -> dict[str, Any]:
        if self.model is None:
            self.load()
        if self.model is None:
            raise RuntimeError(self.load_error or "Detector is not loaded")

        started = time.perf_counter()
        predict_kwargs: dict[str, Any] = {
            "source": image_bgr,
            "conf": self.conf,
            "imgsz": self.image_size,
            "verbose": False,
        }
        if self.device and self.device.lower() != "auto":
            predict_kwargs["device"] = self.device

        with self._lock:
            results = self.model.predict(**predict_kwargs)

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        detections: list[dict[str, Any]] = []

        if results:
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    xyxy = [float(v) for v in box.xyxy[0].tolist()]
                    x1, y1, x2, y2 = xyxy
                    detections.append(
                        {
                            "class_id": class_id,
                            "class_name": CLASS_NAMES.get(class_id, f"class_{class_id}"),
                            "confidence": confidence,
                            "bbox": xyxy,
                            "center": [(x1 + x2) / 2.0, (y1 + y2) / 2.0],
                        }
                    )

        detections.sort(key=lambda item: item["confidence"], reverse=True)
        best = detections[0] if detections else None
        height, width = image_bgr.shape[:2]

        return {
            "model_id": self.model_id,
            "detections": detections,
            "best_detection": best,
            "latency_ms": elapsed_ms,
            "image_width": width,
            "image_height": height,
        }
