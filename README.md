# SMD Vision Inspector

[Türkçe](README.tr.md)

Computer-vision quality inspection for an SMD/SMT placement line. A fixed camera at the
placement machine output inspects every PCB before reflow and alerts the operator when a
component is missing, shifted, rotated, reversed or unexpected. ICs get the strictest checks.

**Status:** early development. No inspection workflow yet.

## Approach

- Deterministic computer vision first: board registration via fiducials, golden-reference
  comparison, template matching, ROI-based checks.
- AI only where it shows a measured advantage over the classical baseline.
- False negatives, false positives and latency are first-class metrics.
- Pipeline stages stay separate: capture → acquisition → registration → inspection →
  decision → alerting, with offline evaluation on recorded inspections.

See [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for scope.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Production images and product recipes are proprietary and not part of this repository.
Tests use synthetic images.
