from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = BACKEND_DIR.parent
REPO_ROOT = DASHBOARD_DIR.parent
load_dotenv(BACKEND_DIR / ".env")


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    model_path: Path = Path(
        os.getenv(
            "WASTENET_MODEL_PATH",
            str(REPO_ROOT / "models" / "detection" / "yolov8n_wastenet_public_assisted_best.pt"),
        )
    )
    model_id: str = os.getenv("WASTENET_MODEL_ID", "yolov8n-public-assisted")
    model_label: str = os.getenv("WASTENET_MODEL_LABEL", "YOLOv8n Public-Assisted")
    device: str = os.getenv("WASTENET_DEVICE", "auto")
    image_size: int = _int("WASTENET_IMAGE_SIZE", 640)
    yolo_conf: float = _float("WASTENET_YOLO_CONF", 0.10)
    sort_conf: float = _float("WASTENET_SORT_CONF", 0.50)
    uncertain_conf: float = _float("WASTENET_UNCERTAIN_CONF", 0.30)
    stable_frames: int = _int("WASTENET_STABLE_FRAMES", 3)
    review_cooldown: float = _float("WASTENET_REVIEW_COOLDOWN", 5.0)
    runtime_dir: Path = Path(os.getenv("WASTENET_RUNTIME_DIR", str(BACKEND_DIR / "runtime")))
    cors_origins_raw: str = os.getenv(
        "WASTENET_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
