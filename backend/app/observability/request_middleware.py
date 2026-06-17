from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response


def add_request_logging_middleware(app: FastAPI, *, slow_request_threshold_ms: float) -> None:
    logger = logging.getLogger("app.observability.http")

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or uuid4().hex
        started_at = perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.exception(
                "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
                request_id,
                method,
                path,
                duration_ms,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        if duration_ms >= slow_request_threshold_ms:
            logger.warning(
                "request_slow request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f threshold_ms=%.2f",
                request_id,
                method,
                path,
                response.status_code,
                duration_ms,
                slow_request_threshold_ms,
            )
        else:
            logger.info(
                "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
                request_id,
                method,
                path,
                response.status_code,
                duration_ms,
            )
        return response
