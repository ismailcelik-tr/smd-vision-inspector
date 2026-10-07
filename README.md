<div align="center">

# SMD Vision Inspector

Deterministic visual inspection for SMD placement lines.

[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue)](LICENSE.md)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA4OCA4OCI%2BPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTAgMGg0MnY0Mkgwek00NiAwaDQydjQySDQ2ek0wIDQ2aDQydjQySDB6TTQ2IDQ2aDQydjQySDQ2eiIvPjwvc3ZnPg%3D%3D)](#development)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://img.shields.io/github/actions/workflow/status/ismailcelik-tr/smd-vision-inspector/ci.yml?branch=main&label=CI)](https://github.com/ismailcelik-tr/smd-vision-inspector/actions/workflows/ci.yml)
[![Last commit](https://img.shields.io/github/last-commit/ismailcelik-tr/smd-vision-inspector)](https://github.com/ismailcelik-tr/smd-vision-inspector/commits/main)

[![English](https://img.shields.io/badge/English-555555?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MCAzMCI%2BPGNsaXBQYXRoIGlkPSJzIj48cGF0aCBkPSJNMCwwdjMwaDYwVjB6Ii8%2BPC9jbGlwUGF0aD48Y2xpcFBhdGggaWQ9InQiPjxwYXRoIGQ9Ik0zMCwxNWgzMHYxNXp2MTVIMHpIMFYwelYwaDMweiIvPjwvY2xpcFBhdGg%2BPGcgY2xpcC1wYXRoPSJ1cmwoI3MpIj48cGF0aCBkPSJNMCwwdjMwaDYwVjB6IiBmaWxsPSIjMDEyMTY5Ii8%2BPHBhdGggZD0iTTAsMEw2MCwzME02MCwwTDAsMzAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSI2Ii8%2BPHBhdGggZD0iTTAsMEw2MCwzME02MCwwTDAsMzAiIGNsaXAtcGF0aD0idXJsKCN0KSIgc3Ryb2tlPSIjQzgxMDJFIiBzdHJva2Utd2lkdGg9IjQiLz48cGF0aCBkPSJNMzAsMHYzME0wLDE1aDYwIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMTAiLz48cGF0aCBkPSJNMzAsMHYzME0wLDE1aDYwIiBzdHJva2U9IiNDODEwMkUiIHN0cm9rZS13aWR0aD0iNiIvPjwvZz48L3N2Zz4%3D&logoSize=auto)](README.md)
[![Türkçe](https://img.shields.io/badge/T%C3%BCrk%C3%A7e-555555?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMCAyMCI%2BPHJlY3Qgd2lkdGg9IjMwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjRTMwQTE3Ii8%2BPGNpcmNsZSBjeD0iMTAuMCIgY3k9IjEwIiByPSI1LjAiIGZpbGw9IiNmZmYiLz48Y2lyY2xlIGN4PSIxMS4yNSIgY3k9IjEwIiByPSI0LjAiIGZpbGw9IiNFMzBBMTciLz48cG9seWdvbiBwb2ludHM9IjE1LjkxNywxMC4wMDAgMTcuNjQ0LDkuNDM5IDE3LjY0NCw3LjYyMiAxOC43MTIsOS4wOTIgMjAuNDM5LDguNTMxIDE5LjM3MiwxMC4wMDAgMjAuNDM5LDExLjQ2OSAxOC43MTIsMTAuOTA4IDE3LjY0NCwxMi4zNzggMTcuNjQ0LDEwLjU2MSIgZmlsbD0iI2ZmZiIvPjwvc3ZnPg%3D%3D&logoSize=auto)](README.tr.md)

</div>

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

## License

[PolyForm Noncommercial 1.0.0](LICENSE.md). Free for noncommercial use. Commercial use
requires a separate license from the copyright holder; open an issue or contact
[@ismailcelik-tr](https://github.com/ismailcelik-tr).
