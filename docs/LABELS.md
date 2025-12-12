# Label Schema

This document describes the labeling conventions used throughout the Stacks monitoring stack.

## Standard Labels

### Core Labels

| Label | Required | Description | Example |
|-------|----------|-------------|---------|
| `job` | Yes | Logical grouping of targets | `stacks` |
| `host` | Yes | Source machine identifier | `stacks-node-1` |
| `service` | Yes | Service within the host | `stacks-node`, `stacks-signer`, `bitcoin` |
| `instance` | Auto | Target address (added by Prometheus) | `localhost:9153` |

### Log-Specific Labels

| Label | Source | Description | Example |
|-------|--------|-------------|---------|
| `level` | Extracted | Log severity level | `info`, `warn`, `error`, `debug` |
| `unit` | Journal | Systemd unit name | `stacks-node.service` |
| `filename` | File | Source log file | `/var/log/stacks/signer.log` |

## Label Values

### job

Use a consistent job name across all Stacks-related metrics:

```
job="stacks"
```

This allows querying all Stacks metrics together while using `service` to differentiate.

### host

Use meaningful, stable hostnames:

```
# Good
host="stacks-prod-1"
host="stacks-testnet"
host="signer-mainnet"

# Bad (too generic)
host="server1"
host="node"

# Bad (contains timestamps or dynamic values)
host="stacks-node-2024-01-15"
```

### service

Standard service names:

| Value | Description |
|-------|-------------|
| `stacks-node` | Stacks blockchain node |
| `stacks-signer` | Stacks signer service |
| `bitcoin` | Bitcoin node (via exporter) |

### level

Log levels extracted from Stacks logs:

| Value | Description |
|-------|-------------|
| `debug` | Detailed debugging information |
| `info` | Normal operational messages |
| `warn` | Warning conditions |
| `error` | Error conditions |
| `critical` | Critical failures (rare) |

## Alloy Relabeling

### Metrics Relabeling

```alloy
// Add consistent labels to scraped metrics
prometheus.relabel "add_labels" {
  forward_to = [prometheus.remote_write.default.receiver]

  rule {
    target_label = "job"
    replacement  = "stacks"
  }

  rule {
    target_label = "host"
    replacement  = env("HOST_LABEL")
  }

  // Service from scrape job
  rule {
    source_labels = ["__meta_scrape_job"]
    target_label  = "service"
  }
}
```

### Log Label Processing

```alloy
// Extract level from Stacks log format
loki.process "extract_level" {
  forward_to = [loki.write.default.receiver]

  // Match: INFO [...] or WARN [...] etc
  stage.regex {
    expression = `^(?P<level>\w+)\s+\[`
  }

  stage.labels {
    values = {
      level = "",
    }
  }

  // Normalize to lowercase
  stage.label_drop {
    values = ["level"]
  }

  stage.template {
    source   = "level"
    template = "{{ ToLower .Value }}"
  }
}
```

## Query Examples

### By Job (All Stacks)

```promql
# All metrics for stacks job
{job="stacks"}

# Up status for all services
up{job="stacks"}
```

### By Host

```promql
# Metrics from specific host
stacks_node_stx_block_height{host="stacks-prod-1"}

# Compare across hosts
stacks_node_stx_block_height{job="stacks"}
```

### By Service

```promql
# Node metrics only
stacks_node_peer_count{service="stacks-node"}

# Signer metrics only
stacks_signer_is_registered{service="stacks-signer"}
```

### Log Queries

```logql
# All Stacks logs
{job="stacks"}

# Errors only
{job="stacks", level="error"}

# Specific host and service
{host="stacks-prod-1", service="stacks-signer"}

# Pattern match in errors
{job="stacks", level="error"} |= "connection refused"
```

## Grafana Variables

Dashboard variables for filtering:

```
# Job variable
label_values(up, job)

# Host variable
label_values(up{job="$job"}, host)

# Service variable
label_values(up{job="$job", host=~"$host"}, service)
```

## Best Practices

### DO

1. **Use lowercase labels**: `level="info"` not `level="INFO"`
2. **Keep cardinality low**: Use enumerated values, not free-form text
3. **Be consistent**: Same label names across metrics and logs
4. **Use service granularity**: Differentiate by service, not port number

### DON'T

1. **Don't include IPs in labels**: Use hostnames instead
2. **Don't include timestamps**: Labels should be static
3. **Don't over-label**: Only add labels you'll filter/group by
4. **Don't use PII**: No email addresses, API keys, etc.

## Label Cardinality

Keep total cardinality manageable:

| Label | Max Values | Notes |
|-------|------------|-------|
| `job` | 1-5 | Typically just `stacks` |
| `host` | <100 | One per monitored server |
| `service` | 3-5 | Fixed set of services |
| `level` | 5 | debug/info/warn/error/critical |

**Target**: < 1000 unique label combinations per metric name

## VictoriaLogs Stream Fields

When using VictoriaLogs, configure stream fields for efficient querying:

```
?_stream_fields=job,host,service,level
```

This enables fast filtering on these high-value labels.
