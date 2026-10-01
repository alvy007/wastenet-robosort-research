from __future__ import annotations

import csv
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import cv2
import numpy as np


class RuntimeStore:
    def __init__(self, runtime_dir: Path, cooldown_seconds: float = 5.0) -> None:
        self.runtime_dir = Path(runtime_dir)
        self.logs_dir = self.runtime_dir / "logs"
        self.review_dir = self.runtime_dir / "review_queue"
        self.uncertain_dir = self.review_dir / "uncertain"
        self.unknown_dir = self.review_dir / "unknown"
        self.detection_log = self.logs_dir / "dashboard_detections.csv"
        self.review_log = self.logs_dir / "dashboard_review_queue.csv"
        self.cooldown_seconds = cooldown_seconds
        self.last_saved = {"uncertain": 0.0, "unknown": 0.0}
        self._lock = Lock()

        for path in (self.logs_dir, self.uncertain_dir, self.unknown_dir):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _append_csv(self, path: Path, header: list[str], row: list[Any]) -> None:
        with self._lock:
            first_write = not path.exists()
            with path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if first_write:
                    writer.writerow(header)
                writer.writerow(row)

    def log_detection(
        self,
        frame_id: int,
        model_id: str,
        decision: dict[str, Any],
        best_detection: dict[str, Any] | None,
        latency_ms: float,
    ) -> None:
        best = best_detection or {}
        bbox = best.get("bbox") or [None, None, None, None]
        self._append_csv(
            self.detection_log,
            [
                "timestamp",
                "frame_id",
                "model_id",
                "action",
                "reason",
                "class_name",
                "confidence",
                "stable_count",
                "mean_stable_confidence",
                "target_bin",
                "latency_ms",
                "x1",
                "y1",
                "x2",
                "y2",
            ],
            [
                self._timestamp(),
                frame_id,
                model_id,
                decision.get("action"),
                decision.get("reason"),
                best.get("class_name"),
                best.get("confidence"),
                decision.get("stable_count"),
                decision.get("mean_stable_confidence"),
                decision.get("target_bin"),
                round(float(latency_ms), 3),
                *bbox,
            ],
        )

    def maybe_save_review(
        self,
        image_bgr: np.ndarray,
        queue_type: str,
        frame_id: int,
        best_detection: dict[str, Any] | None,
        reason: str,
    ) -> dict[str, Any] | None:
        if queue_type not in {"uncertain", "unknown"}:
            return None

        now = time.time()
        if now - self.last_saved[queue_type] < self.cooldown_seconds:
            return None
        self.last_saved[queue_type] = now

        best = best_detection or {}
        class_name = best.get("class_name", "unknown")
        confidence = float(best.get("confidence", 0.0))
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{queue_type}_{stamp}_f{frame_id}_{class_name}_{confidence:.2f}.jpg"
        target_dir = self.uncertain_dir if queue_type == "uncertain" else self.unknown_dir
        path = target_dir / filename
        cv2.imwrite(str(path), image_bgr)

        self._append_csv(
            self.review_log,
            ["timestamp", "frame_id", "queue_type", "filename", "class_name", "confidence", "reason"],
            [self._timestamp(), frame_id, queue_type, filename, class_name, confidence, reason],
        )

        return {
            "filename": filename,
            "queue_type": queue_type,
            "class_name": class_name,
            "confidence": confidence,
            "reason": reason,
        }

    def summary(self) -> dict[str, Any]:
        if not self.detection_log.exists():
            return {
                "records": 0,
                "actions": {},
                "classes": {},
                "avg_latency_ms": None,
            }

        actions: Counter[str] = Counter()
        classes: Counter[str] = Counter()
        latencies: list[float] = []
        records = 0

        with self.detection_log.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                records += 1
                if row.get("action"):
                    actions[row["action"]] += 1
                if row.get("class_name"):
                    classes[row["class_name"]] += 1
                try:
                    latencies.append(float(row["latency_ms"]))
                except (TypeError, ValueError, KeyError):
                    pass

        return {
            "records": records,
            "actions": dict(actions),
            "classes": dict(classes),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        }

    def review_items(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.review_log.exists():
            return []
        items: list[dict[str, Any]] = []
        with self.review_log.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    row["confidence"] = float(row.get("confidence", 0.0))
                except ValueError:
                    row["confidence"] = 0.0
                items.append(row)
        return list(reversed(items[-max(1, min(limit, 500)) :]))
