from __future__ import annotations

from collections import deque
from statistics import mean
from typing import Any


class DecisionEngine:
    """Matches the current research logic: class stability across N frames + confidence gate."""

    def __init__(self, sort_conf: float, uncertain_conf: float, stable_frames: int) -> None:
        self.sort_conf = sort_conf
        self.uncertain_conf = uncertain_conf
        self.stable_frames = max(1, stable_frames)
        self.recent: deque[dict[str, Any]] = deque(maxlen=self.stable_frames)
        self.frame_id = 0

    def reset(self) -> None:
        self.recent.clear()
        self.frame_id = 0

    def evaluate(self, best_detection: dict[str, Any] | None) -> dict[str, Any]:
        self.frame_id += 1

        if best_detection is None:
            self.recent.clear()
            return {
                "frame_id": self.frame_id,
                "action": "NO_DETECTION",
                "reason": "no_detection",
                "target_bin": None,
                "stable_count": 0,
                "required_stable_frames": self.stable_frames,
                "mean_stable_confidence": 0.0,
            }

        self.recent.append(best_detection)
        current_class = best_detection["class_name"]
        stable_count = 0
        stable_confidences: list[float] = []

        for item in reversed(self.recent):
            if item["class_name"] != current_class:
                break
            stable_count += 1
            stable_confidences.append(float(item["confidence"]))

        mean_conf = mean(stable_confidences) if stable_confidences else float(best_detection["confidence"])

        if stable_count >= self.stable_frames and mean_conf >= self.sort_conf:
            action = "SORT"
            reason = "stable_confident_detection"
            target_bin = current_class
        elif float(best_detection["confidence"]) >= self.uncertain_conf:
            action = "WAIT"
            reason = "not_stable_yet" if stable_count < self.stable_frames else "stable_but_below_sort_threshold"
            target_bin = None
        else:
            action = "REVIEW"
            reason = "low_confidence_uncertain"
            target_bin = "admin_review"

        return {
            "frame_id": self.frame_id,
            "action": action,
            "reason": reason,
            "target_bin": target_bin,
            "stable_count": stable_count,
            "required_stable_frames": self.stable_frames,
            "mean_stable_confidence": mean_conf,
            "current_class": current_class,
            "current_confidence": float(best_detection["confidence"]),
        }
