# Grafana Configuration

This directory contains the Grafana dashboard and alert configurations for Stacks monitoring.

## Dashboard

### Import via UI

1. Open Grafana
2. Go to **Dashboards** > **Import**
3. Upload `dashboards/stacks-signer-overview.json`
4. Select your Prometheus and Loki/VictoriaLogs datasources
5. Click **Import**

### Import via Provisioning

Copy files to your Grafana provisioning directory:

```bash
# Create provisioning directories
mkdir -p /etc/grafana/provisioning/dashboards

# Copy dashboard
cp dashboards/stacks-signer-overview.json /var/lib/grafana/dashboards/

# Copy provisioning config
cp provisioning/dashboards.yml.example /etc/grafana/provisioning/dashboards/stacks.yml

# Restart Grafana
systemctl restart grafana-server
```

## Alerts

### Grafana Provisioned Alerts

If using Grafana's built-in alerting:

```bash
# Create provisioning directory
mkdir -p /etc/grafana/provisioning/alerting

# Copy alert rules
cp alerts/stacks-alerts.json /etc/grafana/provisioning/alerting/

# Restart Grafana
systemctl restart grafana-server
```

### Prometheus Alert Rules

If using Prometheus/VictoriaMetrics alerting (recommended for production):

See the [`../prometheus`](../prometheus) directory for Prometheus-format alert rules.

## Dashboard Panels

| Panel | Description | Data Source |
|-------|-------------|-------------|
| **System Gauges** | CPU, Memory, Disk, Load | Prometheus |
| **STX Height** | Current Stacks chain height | Prometheus |
| **BTC Height** | Current Bitcoin block height | Prometheus |
| **Peer Count** | Number of connected peers | Prometheus |
| **Reward Cycle** | Current PoX reward cycle | Prometheus |
| **Alert States** | Current status of all alerts | Grafana |
| **Alert Events** | Timeline of alert firing/resolved | Prometheus |
| **Alert History** | Log history of alert events | Loki |
| **Node Log Volume** | Stacks node log activity breakdown | Loki |
| **Signer Log Volume** | Signer activity breakdown | Loki |
| **Node Logs - WARNs** | Warning-level node logs | Loki |
| **Signer Logs** | Live signer log stream | Loki |

## Variables

The dashboard uses these template variables:

| Variable | Description |
|----------|-------------|
| `host` | Filter by host label |

## Datasource Requirements

The dashboard requires two datasources:

1. **Prometheus/VictoriaMetrics** - For metrics (system gauges, heights, alerts)
2. **Loki/VictoriaLogs** - For logs (log volumes, log panels)

When importing, you'll be prompted to select these datasources.

## Customization

### Change Job Label

If your metrics use a different job label (not `stacks` or `crypto`), update these in the JSON:

```json
{
  "expr": "{job=\"your-job-label\", service=\"stacks-node\"}"
}
```

### Add More Hosts

The `host` variable will automatically discover all hosts with matching metrics. No changes needed.

### Change Time Range

Default time range is 1 hour. To change:
1. Set your preferred time range
2. Save dashboard with "Save current time range as dashboard default" checked
