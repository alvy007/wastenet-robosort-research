MODEL_CATALOG = [
    {
        "id": "yolov8n-local-only",
        "label": "YOLOv8n Local-Only",
        "status": "evaluated",
        "family": "YOLO",
        "precision": 0.710,
        "recall": 0.538,
        "map50": 0.666,
        "map5095": 0.539,
        "notes": "Current local-only baseline on the held-out local test set.",
    },
    {
        "id": "yolov8n-public-assisted",
        "label": "YOLOv8n Public-Assisted",
        "status": "evaluated",
        "family": "YOLO",
        "precision": 0.502,
        "recall": 0.650,
        "map50": 0.647,
        "map5095": 0.529,
        "notes": "Current live dashboard model target. External images were training-only.",
    },
    {
        "id": "yolo26s",
        "label": "YOLO26s",
        "status": "planned",
        "family": "YOLO",
        "precision": None,
        "recall": None,
        "map50": None,
        "map5095": None,
        "notes": "Planned controlled experiment after the interface is stable.",
    },
    {
        "id": "rf-detr-small",
        "label": "RF-DETR-Small",
        "status": "planned",
        "family": "Transformer detector",
        "precision": None,
        "recall": None,
        "map50": None,
        "map5095": None,
        "notes": "Planned controlled experiment after the interface is stable.",
    },
]

CLASSWISE_MAP50 = {
    "classes": ["electronic", "glass", "metal", "others", "paper", "plastic"],
    "yolov8n-local-only": [0.679, 0.354, 0.749, 0.669, 0.669, 0.874],
    "yolov8n-public-assisted": [0.714, 0.350, 0.755, 0.683, 0.484, 0.896],
}

DATASET = {
    "images": {"train": 415, "validation": 85, "test": 96, "total": 596},
    "objects": {
        "electronic": 118,
        "glass": 12,
        "metal": 53,
        "others": 165,
        "paper": 23,
        "plastic": 226,
        "total": 597,
    },
}
