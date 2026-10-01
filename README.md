# WasteNet-RoboSort Research

Publication-oriented research repository for local-domain waste detection, model comparison, decision-gated robotic sorting, and human-in-the-loop dataset improvement.

## Current Baseline

| Experiment | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| YOLOv8n Local-Only | 0.710 | 0.538 | 0.666 | 0.539 |
| YOLOv8n Public-Assisted | 0.502 | 0.650 | 0.647 | 0.529 |

Dataset V1:
- 596 images
- 597 annotated objects
- 415 train
- 85 validation
- 96 test
- 6 classes: electronic, glass, metal, others, paper, plastic

## Current Milestone

Next controlled experiment:

**RF-DETR-Small on the frozen V1 local dataset**

The V1 test set must not be used for tuning, checkpoint selection, augmentation decisions, or active-learning feedback.

## Planned Sequence

1. YOLOv8n Local-Only
2. YOLOv8n Public-Assisted
3. RF-DETR-Small
4. YOLO26-S
5. Error-overlap analysis
6. Dataset V2
7. Hybrid method only if experimentally justified
8. Active-learning round
9. Final dashboard integration
10. Research paper

## Dashboard

The current working research dashboard is available under:

dashboard/

It supports live detection, decision gating, runtime logs, review capture, model comparison, dataset statistics, and a recorded robotic-arm demonstration.
