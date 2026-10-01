# WasteNet Research Dashboard

This folder is the first working interface foundation for the existing WasteNet-RoboSort project.

The current milestone intentionally uses the **existing YOLOv8n public-assisted model**. New model training is postponed until the interface and current runtime pipeline are stable.

## What is included now

- Browser camera input
- FastAPI inference backend
- Ultralytics YOLO detector adapter
- Current three-frame confidence/temporal decision gate
- Live bounding-box overlay
- Class, confidence, latency, FPS estimate, and target-bin display
- Existing YOLOv8 model comparison table
- Dataset distribution panel
- Runtime decision logging
- Uncertain/unknown review queue
- Pre-recorded robotic-arm video panel
- Future-proof model adapter boundary for YOLO26 / RF-DETR later

## Presentation behavior

The robotic arm does **not** need to be connected during the presentation.

Add the final recorded arm demonstration here:

```text
dashboard/frontend/public/robot-arm-demo.mp4
```

The dashboard will play the MP4 from the **Robotic Arm Demonstration** panel while the live section independently performs camera-based detection.

## 1. Copy dashboard into the repository

The expected final structure is:

```text
waste-classification-robot/
├── dashboard/
│   ├── backend/
│   ├── frontend/
│   ├── README.md
│   ├── setup-dashboard.ps1
│   └── run-dashboard.ps1
├── scripts/
├── results/
├── evidence/
└── ...
```

## 2. Configure the current model

From `dashboard/backend`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set the correct model path. The current default is:

```text
E:\Waste_Sorting_Final\models\detection\yolov8n_wastenet_public_assisted_best.pt
```

If your weight is somewhere else, change only `WASTENET_MODEL_PATH`.

Current decision settings match the existing research implementation:

```text
YOLO internal threshold = 0.10
SORT threshold          = 0.50
Uncertain threshold     = 0.30
Stable frames           = 3
Review save cooldown    = 5 seconds
```

## 3. One-time setup on Windows

Open PowerShell in the `dashboard` directory and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup-dashboard.ps1
```

This creates an isolated Python environment for the dashboard backend and installs the frontend packages.

## 4. Start the full interface

```powershell
.\run-dashboard.ps1
```

Two PowerShell windows will open:

- FastAPI backend: `http://127.0.0.1:8000`
- Next.js dashboard: `http://localhost:3000`

Open:

```text
http://localhost:3000
```

Allow camera access when the browser asks for permission.

## 5. Verify the backend first if anything fails

Open:

```text
http://127.0.0.1:8000/api/health
```

A ready system should report:

```json
{
  "ok": true,
  "model_ready": true
}
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Current UI workflow

```text
Browser Camera
    ↓
POST /api/infer
    ↓
Current YOLOv8n Model
    ↓
Best Detection
    ↓
3-Frame Temporal Decision Gate
    ├── SORT
    ├── WAIT
    ├── REVIEW
    └── NO_DETECTION
    ↓
Live UI + Runtime CSV Logs + Review Queue
```

The dashboard currently does not send commands to the physical robot. That is intentional for this presentation phase because the physical arm will be represented by a prerecorded video.

## Runtime data

The backend automatically creates:

```text
dashboard/backend/runtime/
├── logs/
│   ├── dashboard_detections.csv
│   └── dashboard_review_queue.csv
└── review_queue/
    ├── uncertain/
    └── unknown/
```

These runtime files are ignored by Git.

## Current model table

The UI contains the already evaluated models:

- YOLOv8n Local-Only
- YOLOv8n Public-Assisted

It also shows the planned experiment slots without fabricated results:

- YOLO26s
- RF-DETR-Small

Those planned rows will remain empty until the models are actually trained and evaluated on the unchanged local test set.

## Important boundary for the research paper

This dashboard currently reproduces the existing decision logic. It does **not** silently introduce new experimental logic such as IoU stability, tracking, calibration, or per-class thresholds.

Those features should be implemented later as explicit research experiments so that any improvement can be measured fairly.

## Next interface milestones

Before new model training, finish and verify:

1. Current model loads from `.env` without hard-coded machine paths.
2. Browser camera inference works continuously.
3. Bounding boxes align correctly with the live video.
4. SORT / WAIT / REVIEW / NO_DETECTION states behave correctly.
5. Runtime logs are written correctly.
6. Review queue captures low-confidence and unknown cases.
7. Final robotic-arm MP4 plays correctly.
8. UI is presentation-ready at common laptop resolutions.
9. Existing archived research logs can be imported into a historical analytics view.
10. The repo is cleaned so current and legacy scripts are clearly separated.

Only after this milestone is stable should the new model experiments begin.
