# Log-Based Alerting

Prometheus rules can only alert on metrics. Log-silence and log-content alerts require a log backend such as VictoriaLogs or Loki, or a recording rule that turns log counts into metrics.

## VictoriaLogs Provisioning

Use [`grafana/alerts/log-alerts-victorialogs.yaml.example`](../grafana/alerts/log-alerts-victorialogs.yaml.example) when Grafana has a VictoriaLogs datasource installed.

1. Copy the file into Grafana's alert provisioning directory.
2. Replace `VICTORIALOGS_DATASOURCE_UID` with your datasource UID.
3. Restart Grafana or reload provisioning.

The example includes:

| Alert | Window | Purpose |
|-------|--------|---------|
| `stacks-node-log-silence` | 3m + 3m for | Detects node service or log pipeline silence |
| `stacks-signer-log-silence` | 5m + 5m for | Detects signer service or log pipeline silence |
| `bitcoin-node-log-silence` | 10m + 10m for | Detects Bitcoin service or log pipeline silence |
| `stacks-signer-tenure-conflict` | 3m + 1m for | Detects repeated signer tenure warnings |

## Query Contract

The examples assume Alloy sends logs with these labels:

| Label | Values |
|-------|--------|
| `job` | `stacks` by default; adjust queries if you use a different job label |
| `host` | Stable node identifier |
| `service` | `stacks-node`, `stacks-signer`, `bitcoin-node` |
| `level` | `INFO`, `WARN`, `ERROR`, `DEBUG`, `TRACE` when available |

For VictoriaLogs, configure stream fields for efficient filtering:

```text
?_stream_fields=job,host,service,level
```

## Loki Equivalent Queries

If you use Loki alerting instead of VictoriaLogs, the same concepts map to LogQL:

```logql
absent_over_time({service="stacks-node"}[3m])
absent_over_time({service="stacks-signer"}[5m])
absent_over_time({service="bitcoin-node"}[10m])
sum(count_over_time({service="stacks-signer", level="WARN"} |~ "tenure" [3m])) > 5
```

Use `absent_over_time` for silence detection. A bare `sum(count_over_time(...)) < 1` expression may produce no series when logs are absent, which prevents the alert from firing.

Keep these alerts separate from Prometheus rule files unless you first create log-derived metrics.
