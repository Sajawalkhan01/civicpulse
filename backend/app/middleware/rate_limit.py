from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.providers.rate_limiter import RateLimitExceeded, get_rate_limiter

_LIMITED_METHOD = "POST"
_LIMITED_PATH = "/api/complaints"


def _client_ip(request: Request) -> str:
    """request.client.host is only the real caller's IP until nginx sits in
    front of the backend (a later chunk); after that it's the proxy's own IP
    on every single request, no matter who actually made it. nginx appends
    the true client IP as the LAST entry of X-Forwarded-For as a request
    passes through it -- everything before that last hop is whatever the
    client itself chose to send in that header and is trivially forged, so
    only the last, proxy-appended hop can be trusted to key the rate limit
    by."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        last_hop = forwarded.split(",")[-1].strip()
        if last_hop:
            return last_hop
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies the distributed Redis rate limiter to POST /api/complaints
    only -- every other route passes straight through."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != _LIMITED_METHOD or request.url.path != _LIMITED_PATH:
            return await call_next(request)

        try:
            get_rate_limiter().check(_client_ip(request))
        except RateLimitExceeded as exc:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "message": "Too many requests"},
                headers={"Retry-After": str(exc.retry_after_seconds)},
            )
        return await call_next(request)
