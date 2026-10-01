from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .decision_engine import DecisionEngine
from .detectors import UltralyticsDetector
from .metrics import CLASSWISE_MAP50, DATASET, MODEL_CATALOG
from .runtime_store import RuntimeStore


detector = UltralyticsDetector(
    model_path=settings.model_path,
    model_id=settings.model_id,
    model_label=settings.model_label,
    image_size=settings.image_size,
    conf=settings.yolo_conf,
    device=settings.device,
)
decision_engine = DecisionEngine(
    sort_conf=settings.sort_conf,
    uncertain_conf=settings.uncertain_conf,
    stable_frames=settings.stable_frames,
)
store = RuntimeStore(settings.runtime_dir, settings.review_cooldown)


@asynccontextmanager
async def lifespan(_: FastAPI):
    detector.load()
    yield


app = FastAPI(
    title="WasteNet Research Dashboard API",
    version="0.1.0",
    description="Live inference, decision-gating, metrics, and review-queue API for WasteNet-RoboSort.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"name": "WasteNet Research Dashboard API", "docs": "/docs"}


@app.get("/api/health")
def health() -> dict:
    status = detector.status()
    return {
        "ok": True,
        "model_ready": status["loaded"],
        "model": status,
        "runtime_dir": str(settings.runtime_dir),
    }


@app.get("/api/models")
def models() -> dict:
    live = detector.status()
    items = []
    for model in MODEL_CATALOG:
        item = dict(model)
        item["active"] = model["id"] == settings.model_id
        if item["active"]:
            item["runtime_loaded"] = live["loaded"]
            item["runtime_model_path"] = live["model_path"]
        items.append(item)
    return {"active_model_id": settings.model_id, "items": items}


@app.get("/api/metrics")
def metrics() -> dict:
    return {
        "models": MODEL_CATALOG,
        "classwise_map50": CLASSWISE_MAP50,
        "dataset": DATASET,
    }


@app.get("/api/settings")
def decision_settings() -> dict:
    return {
        "yolo_conf": settings.yolo_conf,
        "sort_conf": settings.sort_conf,
        "uncertain_conf": settings.uncertain_conf,
        "stable_frames": settings.stable_frames,
        "image_size": settings.image_size,
        "review_cooldown_seconds": settings.review_cooldown,
    }


@app.get("/api/logs/summary")
def log_summary() -> dict:
    return store.summary()


@app.get("/api/review")
def review_queue(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> dict:
    return {"items": store.review_items(limit)}


@app.post("/api/reset")
def reset_session() -> dict:
    decision_engine.reset()
    return {"ok": True, "message": "Live decision state reset."}


@app.post("/api/infer")
async def infer(frame: Annotated[UploadFile, File(description="JPEG or PNG camera frame")]) -> dict:
    raw = await frame.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image upload")

    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    try:
        prediction = detector.predict(image)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    decision = decision_engine.evaluate(prediction["best_detection"])
    frame_id = int(decision["frame_id"])

    review_item = None
    if decision["action"] == "REVIEW":
        review_item = store.maybe_save_review(
            image,
            "uncertain",
            frame_id,
            prediction["best_detection"],
            decision["reason"],
        )
    elif decision["action"] == "NO_DETECTION":
        review_item = store.maybe_save_review(
            image,
            "unknown",
            frame_id,
            prediction["best_detection"],
            decision["reason"],
        )

    store.log_detection(
        frame_id,
        prediction["model_id"],
        decision,
        prediction["best_detection"],
        prediction["latency_ms"],
    )

    fps_estimate = 1000.0 / prediction["latency_ms"] if prediction["latency_ms"] > 0 else None
    return {
        **prediction,
        "decision": decision,
        "review_item": review_item,
        "fps_estimate_from_inference": fps_estimate,
    }
