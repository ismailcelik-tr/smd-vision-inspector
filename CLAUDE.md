# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project State

Pre-MVP. Scaffolding only; no inspection pipeline yet.

`PROJECT_BRIEF.md` is the source of truth for scope, defect types, and
long-term capabilities. Read it before planning work.

## Commands

```bash
uv sync                                  # install
uv run pytest                            # all tests
uv run pytest tests/test_log.py::test_filters_below_level   # single test
uv run pytest -m real_data               # local-only, needs samples/
uv run ruff check . && uv run ruff format --check .
uv run mypy                              # strict
```

Production target is Windows; CI runs on Windows and Ubuntu.

## Language

- Repo is public on GitHub. All committed content is English.
- A Turkish README (`README.tr.md`, linked from `README.md`) is the only
  planned Turkish file.

## Data

Production PCB images, datasets, and real product recipes are proprietary.
They live in gitignored `samples/`, `datasets/`, and `recipes.local/`.
Tests use synthetic images only.

These paths are symlinks to a folder synced outside git; `SYNC.local.md`
(gitignored) describes the setup. If it is missing on a fresh clone, ask
the user for the sync folder path.

## Architecture Constraints

Pipeline stages stay separate components with clean interfaces:

```
capture → registration → inspection → decision → alerting
                                         ↓
                                    evaluation
```

- Camera I/O stays behind a driver abstraction; inspection logic never
  touches raw camera APIs.
- Inspection is configuration-driven per PCB/product variant.

## Engineering Approach

- Deterministic CV first: registration, geometric comparison, image
  differencing, template matching, ROI-based checks.
- Introduce AI/deep learning only with a measured advantage over the
  classical baseline. Back the claim with evaluation results.
- False negatives, false positives, and latency are first-class metrics.
  Changes affecting detection should report their impact on them.
