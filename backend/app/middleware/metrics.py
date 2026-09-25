import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.metrics import REQUEST_COUNT, REQUEST_LATENCY


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started

        route = request.scope.get("route")
        path = route.path if route is not None else request.url.path

        REQUEST_COUNT.labels(
            method=request.method, path=path, status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)
        return response
