# Integration Notes

## Current scope

This milestone deliberately decouples the live presentation UI from physical robot control.

- Live: camera -> model -> decision gate -> dashboard
- Recorded: physical robotic-arm demonstration video
- Disabled for presentation milestone: live TCP command transmission to the robotic arm

This avoids the existing port/protocol mismatch between the current `scripts/vision_server.py` and the archived robot client scripts.

## Existing repository mismatch to fix later

Current research vision server:

```text
scripts/vision_server.py -> 127.0.0.1:9999
```

Archived robot clients:

```text
robot/control_scripts/robot_controller.py -> 127.0.0.1:65432
robot/control_scripts/robot_simulation.py -> 127.0.0.1:65432
```

The connection lifecycle also differs. Do not connect these files directly until one shared protocol is defined.

## Why the dashboard uses browser camera input

The browser owns the webcam and sends compressed frames to FastAPI. This gives the presentation interface direct control of:

- camera start/stop
- live preview
- bounding-box overlay
- future model switching

It also avoids a second OpenCV window and makes the demo feel like one integrated research application.

## Future detector adapter

The backend defines a minimal detector boundary in:

```text
backend/app/detectors/base.py
```

The current implementation is:

```text
backend/app/detectors/ultralytics_detector.py
```

Later model families should implement the same output contract:

```text
model_id
detections[]
best_detection
latency_ms
image_width
image_height
```

This allows YOLO26 and RF-DETR to be added without rewriting the dashboard.
