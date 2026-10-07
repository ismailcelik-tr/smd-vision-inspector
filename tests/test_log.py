import io
import json
import logging

import structlog

from smd_vision_inspector.log import configure_logging


def _records(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_emits_json_with_context() -> None:
    stream = io.StringIO()
    configure_logging(stream=stream)

    structlog.get_logger().info("board_inspected", board_id=7, verdict="PASS")

    [record] = _records(stream)
    assert record["event"] == "board_inspected"
    assert record["level"] == "info"
    assert record["board_id"] == 7
    assert record["verdict"] == "PASS"
    assert "timestamp" in record


def test_filters_below_level() -> None:
    stream = io.StringIO()
    configure_logging(level=logging.WARNING, stream=stream)

    log = structlog.get_logger()
    log.info("ignored")
    log.warning("kept")

    assert [r["event"] for r in _records(stream)] == ["kept"]
