# SMD Vision Inspector — Project Brief

> Status: brief only. No inspection workflow is implemented yet.

## Purpose

Computer-vision-based quality inspection for a factory SMD/SMT production
line.

A pick-and-place machine outputs PCBs with placed components. A fixed camera
at the machine output inspects every PCB after placement.

**Primary goal:** detect misplaced components, with emphasis on ICs.

When a defect is detected, the operator must be notified immediately.

## Defect Types

- Missing component
- Wrong component
- Wrong component position
- Rotated component
- Wrong IC orientation (polarity / pin-1)
- Shifted component
- Unexpected (extra) component
- Visually anomalous component
- Other placement-related defects

## Long-Term Capabilities

- Fixed industrial cameras
- Multiple PCB / product variants
- Board detection
- Image alignment / registration
- Component-level inspection
- Reference-based inspection
- AI-based inspection where classical CV falls short
- Confidence scoring
- Operator alerts
- Image logging
- Inspection history
- Replay
- Evaluation
- Latency measurement
- Observability
- PLC / machine integration (future)

## Initial Technology Direction

- Python, with type hints
- OpenCV
- pytest
- Modern Python packaging
- Structured logging
- Configuration-driven inspection

## Engineering Principles

### Deterministic CV first

Do not assume AI / deep learning is the best solution by default.

The first MVP must investigate how much of the problem deterministic
computer vision can solve, using techniques such as:

- Board registration
- Geometric comparison
- Image differencing
- Template matching
- ROI-based inspection

AI is introduced only where it provides a **measurable** advantage.

### Production-grade concerns

The system targets real factory use. The following matter:

- False negatives (missed defects)
- False positives (false alarms)
- Latency
- Reliability
- Explainability
- Maintainability

### Separation of concerns

The long-term architecture keeps these as separate components:

```
capture → registration → inspection → decision → alerting
                                         ↓
                                    evaluation
```

## Reference Material

Sample PCB images from the production environment represent real cases and
serve as reference material for understanding the visual inspection problem.
They are not yet in this repository.
