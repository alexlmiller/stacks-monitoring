# Stacks Monitoring

Production-ready monitoring stack for **Stacks Node**, **Stacks Signer**, and **Bitcoin Node** with Grafana dashboards, Prometheus alerts, and log processing pipelines.

![OSS Stacks Signer Dash](https://github.com/user-attachments/assets/384c3111-7993-44df-b2e3-b8894ec87ad3)

## Features

- **Grafana Dashboard** - Comprehensive view of node health, signer activity, and log analysis
- **PoX Cycle Exporter** - Prometheus metrics for stacking cycle monitoring and restack deadline alerts
- **Prometheus Alert Rules** - Pre-configured node, signer, Bitcoin, and PoX alerts
- **Grafana Alloy Pipelines** - Log collection, parsing, and field extraction for Stacks logs
- **Multiple Deployment Options** - Docker or systemd
- **Flexible Backend Support** - Works with Prometheus/VictoriaMetrics and Loki/VictoriaLogs

## Quick Start

### Prerequisites

- Running Stacks Node, Stacks Signer, and/or Bitcoin Node
- Grafana 10+ with either:
  - Prometheus or VictoriaMetrics (for metrics)
  - Loki or VictoriaLogs (for logs)
- Grafana Alloy 1.x (for log collection)

### 1. Import the Dashboard

1. Download [`grafana/dashboards/stacks-signer-overview.json`](grafana/dashboards/stacks-signer-overview.json)
2. In Grafana: **Dashboards** > **Import** > Upload JSON
3. Select your Prometheus/VictoriaMetrics datasource and a Loki-compatible logs datasource. If you use VictoriaLogs for dashboard log panels, expose it through its Loki-compatible query endpoint and select it as a Loki datasource.
4. Click **Import**

### 2. Add Alert Rules

**For Prometheus/VictoriaMetrics:**
```bash
cp prometheus/alerts/stacks.rules.yml /etc/prometheus/rules/
# Reload Prometheus
```

**For Grafana Alerting:**
```bash
cp grafana/alerts/stacks-alerts.yaml /etc/grafana/provisioning/alerting/
# Optional VictoriaLogs log-based alerts:
# cp grafana/alerts/log-alerts-victorialogs.yaml.example /etc/grafana/provisioning/alerting/log-alerts-victorialogs.yaml
# Restart Grafana
```

### 3. Set Up Log Collection

Choose your deployment method:

**Docker:**
```bash
cd docker
cp .env.example .env
# Edit .env with your endpoints
docker-compose -f docker-compose.node.yml up -d
```

**Systemd:**
```bash
# Install Alloy (see docs/INSTALLATION.md)
cp alloy/examples/node-vm-complete.alloy /etc/alloy/config.alloy
# Edit config with your endpoints
systemctl enable --now alloy
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Your Node Server                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Stacks Node  │  │Stacks Signer │  │ Bitcoin Node │  │PoX Exporter │  │
│  │  :20443      │  │   :30000     │  │   :8332      │  │   :9816 📊  │  │
│  │  :9153 📊    │  │   :30001 📊  │  │   :9332 📊   │  └──────┬──────┘  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │         │
│         │                 │                  │                 │         │
│         └────────────┬────┴──────────────────┴─────────────────┘         │
│                      │                                                   │
│              ┌───────▼───────┐                                           │
│              │  Alloy Agent  │  Collects metrics & logs                  │
│              │    :12345     │  Parses Stacks log format                 │
│              └───────┬───────┘                                           │
│                      │                                                   │
└──────────────────────┼───────────────────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌─────────────────┐       ┌─────────────────┐
│ Prometheus or   │       │   Loki or       │
│ VictoriaMetrics │       │ VictoriaLogs    │
│     :9090       │       │    :3100        │
└────────┬────────┘       └────────┬────────┘
         │                         │
         └───────────┬─────────────┘
                     │
              ┌──────▼──────┐
              │   Grafana   │
              │    :3000    │
              └─────────────┘
```

## Components

### Dashboard Panels

| Panel | Description |
|-------|-------------|
| System Gauges | CPU, Memory, Disk, Load |
| STX/BTC Height | Local Stacks and Bitcoin chain heights |
| Peer Count | Total inbound and outbound Stacks peer connections |
| Reward Cycle / To Next Cycle | Current signer reward cycle and optional PoX countdown |
| Node Log Volume | Stacks node log activity breakdown |
| Signer Log Volume | Signer activity (proposals, validations, accepts/rejects) |
| Alert States | Current status of all Stacks-related alerts |
| Alert Timeline | Visual history of alert firing/resolved events |
| Node Logs - WARNs | Filtered view of warning-level node logs |
| Signer Logs | Live signer log stream |

### Alert Rules

| Alert | Severity | Condition |
|-------|----------|-----------|
| StacksSignerDown | Critical | Signer metrics unreachable for 3 minutes |
| StacksSignerHighRejection | Warning | Block rejection rate > 50% |
| StacksSignerNotRegistered | Warning | Signer not registered for current cycle |
| StacksSignerStateConflicts | Warning | State machine conflicts detected |
| StacksSignerSlowResponse | Warning | 95th percentile response time > 60s |
| StacksNodeLowPeers | Warning | Fewer than 10 peer connections |
| StacksRestackReminder | Warning | <720 blocks (~5 days) until prepare phase |
| StacksRestackUrgent | Critical | <144 blocks (~1 day) until prepare phase |
| StacksPoXExporterDown | Warning | PoX exporter unreachable for 5 minutes |
| StacksPoXApiUnreachable | Warning | Cannot reach Stacks node /v2/pox API |

Log-silence alerts require Loki/VictoriaLogs alerting or a log-derived metric; they are documented separately instead of included in Prometheus rule files.

### Intentional Scope

This package does not compare your local Stacks node height against the Hiro public API. Dashboards and alerts are designed around telemetry from your own node, signer, Bitcoin node, and optional local exporters. Public APIs may still be used by optional exporters when they provide data your node does not expose directly, such as PoX registration lookups.

### Log Parsing Pipeline

The Alloy configuration parses Stacks' Rust log format:
```
LEVEL [timestamp] [file:line] [context] message, key: value, ...
```

**Extracted Labels:**
- `level` - INFO, WARN, ERROR, DEBUG
- `source_file` - Rust source file and line number
- `component` - Log context (e.g., `p2p`, `signer_runloop`)
- `block_height` - Current block height
- `tx_id` - Transaction hash
- `block_id` - Block hash
- `peer_addr` - Peer IP address
- `signer_sig_hash` - Signer signature hash
- `stackerdb_name` - StackerDB contract name

## Metrics Reference

### Stacks Node Metrics (port 9153)

| Metric | Description |
|--------|-------------|
| `stacks_node_stacks_tip_height` | Current Stacks chain height |
| `stacks_node_burn_block_height` | Current Bitcoin block height |
| `stacks_node_neighbors_outbound` | Number of outbound Stacks peers |
| `stacks_node_neighbors_inbound` | Number of inbound Stacks peers |

### Stacks Signer Metrics (port 30001)

| Metric | Description |
|--------|-------------|
| `stacks_signer_block_responses_sent` | Block responses by type (accepted/rejected) |
| `stacks_signer_agreement_state_conflicts` | State machine conflict count |
| `stacks_signer_current_reward_cycle` | Current PoX reward cycle |
| `stacks_signer_is_registered` | Registration status (1=registered) |
| `stacks_signer_block_response_latencies_histogram` | Response time distribution |

### Bitcoin Exporter Metrics (port 9332)

| Metric | Description |
|--------|-------------|
| `bitcoin_blocks` | Current Bitcoin block height |
| `bitcoin_difficulty` | Current mining difficulty |
| `bitcoin_conn_in` / `bitcoin_conn_out` | Number of inbound/outbound peers |

### PoX Exporter Metrics (port 9816)

| Metric | Description |
|--------|-------------|
| `stacks_pox_up` | 1 if Stacks node API is reachable |
| `stacks_pox_blocks_until_prepare_phase` | Blocks until next prepare phase |
| `stacks_pox_blocks_until_reward_phase` | Blocks until next reward phase |
| `stacks_pox_current_cycle` | Current PoX cycle number |
| `stacks_pox_next_cycle` | Next PoX cycle number |
| `stacks_pox_current_burn_height` | Current Bitcoin block height |
| `stacks_pox_cycle_length` | PoX cycle length (2100 blocks) |

See [exporters/pox-exporter/README.md](exporters/pox-exporter/README.md) for full metrics documentation.

## Configuration

### Environment Variables (Docker)

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_TARGET_URL` | - | Prometheus/VictoriaMetrics write endpoint |
| `LOGS_TARGET_URL` | - | Loki/VictoriaLogs push endpoint |
| `STACKS_NODE_METRICS` | `localhost:9153` | Stacks node metrics endpoint |
| `STACKS_SIGNER_METRICS` | `localhost:30001` | Stacks signer metrics endpoint |
| `BITCOIN_METRICS` | `localhost:9332` | Bitcoin exporter endpoint |
| `POX_EXPORTER_METRICS` | `localhost:9816` | PoX exporter endpoint |
| `STACKS_NODE_URL` | `http://localhost:20443` | Stacks node RPC (for PoX exporter) |
| `POX_EXPORTER_LISTEN_ADDRESS` | `0.0.0.0` | Address for PoX exporter to bind |
| `HOST_LABEL` | `stacks-node` | Host label for metrics/logs |

### Alloy Configuration

See [`alloy/README.md`](alloy/README.md) for detailed configuration options.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system design
- [Metrics Reference](docs/METRICS.md) - Complete metrics documentation
- [Label Schema](docs/LABELS.md) - Labeling conventions
- [Log-Based Alerting](docs/LOG_ALERTING.md) - VictoriaLogs/Loki alert examples
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Stacks Foundation](https://stacks.org/) for the Stacks blockchain
- [Grafana Labs](https://grafana.com/) for Grafana, Alloy, and Loki
- [VictoriaMetrics](https://victoriametrics.com/) for VictoriaMetrics and VictoriaLogs
