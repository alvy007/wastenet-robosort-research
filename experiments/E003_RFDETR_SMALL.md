# E003 - RF-DETR-Small

## Objective

Evaluate RF-DETR-Small on the same frozen V1 local dataset before any Dataset V2 modification.

## Dataset

Train: 415 images  
Validation: 85 images  
Test: 96 images  
Classes: 6

Local prepared dataset:

E:\Waste_Sorting_Final\data\rfdetr_dataset

Kaggle archive:

E:\Waste_Sorting_Final\kaggle_upload\rfdetr_wastenet_local.zip

## Rules

1. Train only on V1 train.
2. Select checkpoint only using validation.
3. Freeze configuration before test evaluation.
4. Preserve predictions for later model-error comparison.

## Metrics

- Precision
- Recall
- mAP50
- mAP50-95
- class-wise AP
- inference latency
- model size
- checkpoint epoch
- training duration

## Status

Ready for training.
