from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

# Declared now, populated once the real triage provider (providers/triage/)
# lands in the next chunk.
TRIAGE_LATENCY_SECONDS = Histogram(
    "triage_latency_seconds",
    "Latency of triage provider calls in seconds",
)

TRIAGE_FALLBACK_TOTAL = Counter(
    "triage_fallback_total",
    "Number of times triage fell back to a secondary/rules-based provider",
)
