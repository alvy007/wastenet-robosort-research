# Dataset Policy

## Dataset V1

Frozen for controlled model comparison.

- 596 images
- 597 objects
- 415 train
- 85 validation
- 96 test

## Dataset V2

Dataset V2 will be created separately.

Possible work:
- annotation audit
- duplicate removal
- raw-image recovery
- targeted local image collection
- class balancing
- licensed external data
- object/session-aware splitting
- train-only augmentation

## Important

Dataset V1 must never be overwritten.

Validation and test data remain untouched by augmentation.

External data must have traceable source and license information.
