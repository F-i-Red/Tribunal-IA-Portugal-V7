"""
Logger estruturado V7 — structlog + fallback stdlib
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Optional

try:
    import structlog
    STRUCTLOG_OK = True
except ImportError:
    STRUCTLOG_OK = False

_logger_inst: Optional["TribunalLogger"] = None
_logger_lock = threading.Lock()


class TribunalLogger:
    def __init__(self) -> None:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        if STRUCTLOG_OK:
            structlog.configure(
                wrapper_class=structlog.make_filtering_bound_logger(level),
                logger_factory=structlog.PrintLoggerFactory(),
            )
            self._log = structlog.get_logger("tribunal_ia")
        else:
            logging.basicConfig(
                level=level,
                format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            )
            self._log = logging.getLogger("tribunal_ia")

    def info(self, msg: str, **kw: Any) -> None:
        if STRUCTLOG_OK:
            self._log.info(msg, **kw)
        else:
            self._log.info(msg)

    def warning(self, msg: str, **kw: Any) -> None:
        if STRUCTLOG_OK:
            self._log.warning(msg, **kw)
        else:
            self._log.warning(msg)

    def error(self, msg: str, **kw: Any) -> None:
        if STRUCTLOG_OK:
            self._log.error(msg, **kw)
        else:
            self._log.error(msg)

    def debug(self, msg: str, **kw: Any) -> None:
        if STRUCTLOG_OK:
            self._log.debug(msg, **kw)
        else:
            self._log.debug(msg)

    def log_api_call(
        self,
        modelo: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: float,
    ) -> None:
        self.info(
            "api_call",
            modelo=modelo,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=round(duration_ms, 1),
        )


def get_logger() -> TribunalLogger:
    global _logger_inst
    with _logger_lock:
        if _logger_inst is None:
            _logger_inst = TribunalLogger()
    return _logger_inst
