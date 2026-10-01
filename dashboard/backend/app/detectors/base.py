from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseDetector(ABC):
    """Minimal detector contract so future model families can plug into the dashboard."""

    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def predict(self, image_bgr: np.ndarray) -> dict[str, Any]:
        raise NotImplementedError
