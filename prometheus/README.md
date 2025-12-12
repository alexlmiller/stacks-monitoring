# Prometheus Configuration

This directory contains Prometheus alert rules and scrape configuration examples for Stacks monitoring.

## Alert Rules

Copy `alerts/stacks.rules.yml` to your Prometheus rules directory:

```bash
# For Prometheus
cp alerts/stacks.rules.yml /etc/prometheus/rules/

# Verify syntax
promtool check rules /etc/prometheus/rules/stacks.rules.yml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
# OR
systemctl reload prometheus
```

### Alert Summary

| Alert | Severity | Condition |
|-------|----------|-----------|
| **StacksSignerDown** | Critical | Signer metrics unreachable for 3m |
| **StacksNodeDown** | Critical | Node metrics unreachable for 3m |
| **BitcoinNodeDown** | Critical | Bitcoin metrics unreachable for 3m |
| **StacksSignerHighRejection** | Warning | Block rejection rate > 50% |
| **StacksSignerNotRegistered** | Warning | Signer not registered for cycle |
| **StacksSignerStateConflicts** | Warning | State machine conflicts detected |
| **StacksSignerSlowResponse** | Warning | 95th percentile latency > 60s |
| **StacksNodeLowPeers** | Warning | Peer count < 10 |
| **BitcoinBlockStall** | Warning | No new block for 30 minutes |
| **StacksSignerLogSilence** | Warning | No logs for 3 minutes |

## Scrape Configuration

Add these jobs to your `prometheus.yml`:

```yaml
scrape_configs:
  # Stacks Node metrics
  - job_name: 'stacks-node'
    static_configs:
      - targets: ['your-node:9153']
        labels:
          host: 'stacks-node'
          service: 'stacks-node'

  # Stacks Signer metrics
  - job_name: 'stacks-signer'
    static_configs:
      - targets: ['your-node:30001']
        labels:
          host: 'stacks-node'
          service: 'stacks-signer'

  # Bitcoin exporter metrics
  - job_name: 'bitcoin-node'
    static_configs:
      - targets: ['your-node:9332']
        labels:
          host: 'stacks-node'
          service: 'bitcoin-node'
```

### Using Alloy Instead

If you're using Grafana Alloy for metric collection (recommended), you don't need these scrape configs in Prometheus. Alloy will scrape and forward metrics directly.

See the [`../alloy`](../alloy) directory for Alloy configurations.

## VictoriaMetrics

These alert rules are compatible with VictoriaMetrics and vmalert. To use with vmalert:

```bash
# Copy rules
cp alerts/stacks.rules.yml /etc/vmalert/rules/

# Start vmalert with rules
vmalert -rule="/etc/vmalert/rules/*.yml" \
        -datasource.url="http://victoriametrics:8428" \
        -notifier.url="http://alertmanager:9093"
```

## Alertmanager Configuration

Example Alertmanager route for Stacks alerts:

```yaml
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    - match_re:
        service: 'stacks.*|bitcoin.*'
      receiver: 'stacks-alerts'
      group_by: ['alertname', 'host']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h

receivers:
  - name: 'stacks-alerts'
    slack_configs:
      - channel: '#stacks-alerts'
        title: '{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
```
