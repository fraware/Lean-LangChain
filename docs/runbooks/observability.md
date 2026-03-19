# Observability runbook

Prometheus metrics, alert examples, and minimal dashboard guidance for the Lean Gateway. The Gateway exposes `GET /metrics` when `OBR_METRICS_ENABLED=1`; install the metrics extra (`pip install lean-langchain-gateway[metrics]`) and point Prometheus at the Gateway.

## Metrics

The Gateway exposes `GET /metrics` (Prometheus text format) when `OBR_METRICS_ENABLED=1`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `obr_http_requests_total` | Counter | `method`, `path`, `status_class` | Total HTTP requests (status_class: 2xx, 4xx, 5xx). |
| `obr_http_request_duration_seconds` | Histogram | `method`, `path` | Request latency; buckets 0.01–5s. |

Use these for rate, error ratio, and latency (e.g. p50, p95, p99).

---

## Prometheus alert example

Below is a minimal example; adapt to your Prometheus/Alertmanager setup.

```yaml
# Example: save as prometheus-alerts-obr.example.yaml and include in your Prometheus config.
groups:
  - name: obligation-gateway
    rules:
      # Gateway returning 5xx
      - alert: GatewayHigh5xxRate
        expr: |
          sum(rate(obr_http_requests_total{status_class="5xx"}[5m])) by (path)
            /
          sum(rate(obr_http_requests_total[5m])) by (path)
          > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Gateway 5xx rate above 5% on {{ $labels.path }}"

      # Readiness failure (if you expose readiness as a metric or scrape /ready)
      # Alternative: alert on target down or health check failure in your orchestration.
      - alert: GatewayTargetDown
        expr: up{job="obligation-gateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Gateway target down or not scraping"
```

---

## Minimal dashboard (Grafana-style)

If using Grafana (or similar), create a dashboard with:

1. **Request rate** — `sum(rate(obr_http_requests_total[5m])) by (path)` (graph or stat).
2. **Error rate** — `sum(rate(obr_http_requests_total{status_class="5xx"}[5m])) / sum(rate(obr_http_requests_total[5m]))` (gauge or graph).
3. **Latency p95** — `histogram_quantile(0.95, sum(rate(obr_http_request_duration_seconds_bucket[5m])) by (le, path))` (graph by path).
4. **Latency p50** — same with `0.5` quantile.

Panel titles: e.g. "Gateway request rate", "Gateway 5xx ratio", "Gateway p95 latency". No dashboard JSON is committed; define in your Grafana or provisioning.

---

## Logs and traces

- **Logs:** Gateway logs JSON to stdout (`timestamp`, `level`, `message`, `request_id`). Ship via your log agent (e.g. Fluentd, Datadog, CloudWatch). Use `request_id` to correlate with traces and metrics.
- **Traces:** Set `OBR_OTLP_ENDPOINT` or `LANGCHAIN_API_KEY` for OTLP or LangSmith. See [running.md](../running.md) and [deployment.md](../deployment.md).

**See also:** [running.md](../running.md) (Logs and traces), [deployment.md](../deployment.md) (Observability).
