# Experiment Registry

## Frozen Dataset V1

- Train: 415
- Validation: 85
- Test: 96
- Classes: 6

## Experiments

| ID | Model | Training Data | Status | Result |
|---|---|---|---|---|
| E001 | YOLOv8n Local-Only | V1 local | Complete | P=0.710, R=0.538, mAP50=0.666, mAP50-95=0.539 |
| E002 | YOLOv8n Public-Assisted | Local + public support | Complete | P=0.502, R=0.650, mAP50=0.647, mAP50-95=0.529 |
| E003 | RF-DETR-Small Local | V1 local | Next | Pending |
| E004 | YOLO26-S Local | V1 local | Planned | Pending |
| E005 | Error Complementarity Analysis | E001-E004 | Planned | Pending |
| E006 | Dataset V2 Baseline | V2 | Planned | Pending |
| E007 | Proposed Hybrid | TBD | Conditional | Pending |
| E008 | Active-Learning Round 1 | Reviewed hard cases | Planned | Pending |

## Required for Every Experiment

Record:
- experiment ID
- dataset version
- exact split
- model
- pretrained checkpoint
- resolution
- epochs
- batch size
- optimizer
- learning rate
- augmentation
- seed
- early stopping
- best checkpoint rule
- validation metrics
- final test metrics
- per-class metrics
- inference latency
- training environment
- notes

## Test Set Rule

The test set is never used for:
- threshold tuning
- checkpoint selection
- augmentation decisions
- architecture selection
- active-learning feedback
