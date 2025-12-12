# Stacks Monitoring

Production-ready monitoring stack for **Stacks Node**, **Stacks Signer**, and **Bitcoin Node** with Grafana dashboards, Prometheus alerts, and log processing pipelines.

## Features

- **Grafana Dashboard** - Comprehensive view of node health, signer activity, and log analysis
- **Prometheus Alert Rules** - 8 pre-configured alerts for common issues
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
3. Select your Prometheus and Loki/VictoriaLogs datasources
4. Click **Import**

### 2. Add Alert Rules

**For Prometheus/VictoriaMetrics:**
```bash
cp prometheus/alerts/stacks.rules.yml /etc/prometheus/rules/
# Reload Prometheus
```

**For Grafana Alerting:**
```bash
cp grafana/alerts/stacks-alerts.json /etc/grafana/provisioning/alerting/
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
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Node Server                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Stacks Node  │  │Stacks Signer │  │ Bitcoin Node │              │
│  │  :20443      │  │   :30000     │  │   :8332      │              │
│  │  :9153 📊    │  │   :30001 📊  │  │   :9332 📊   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                      │
│         └────────────┬────┴──────────────────┘                      │
│                      │                                              │
│              ┌───────▼───────┐                                      │
│              │  Alloy Agent  │  Collects metrics & logs             │
│              │    :12345     │  Parses Stacks log format            │
│              └───────┬───────┘                                      │
│                      │                                              │
└──────────────────────┼──────────────────────────────────────────────┘
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
| StacksSignerLogSilence | Warning | No signer logs for 3 minutes |
| StacksNodeLowPeers | Warning | Fewer than 10 peer connections |
| BitcoinBlockStall | Warning | No new Bitcoin block for 30 minutes |

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
| `stacks_node_peer_count` | Number of connected peers |

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
| `bitcoin_peers` | Number of connected peers |

## Configuration

### Environment Variables (Docker)

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_TARGET_URL` | - | Prometheus/VictoriaMetrics write endpoint |
| `LOGS_TARGET_URL` | - | Loki/VictoriaLogs push endpoint |
| `STACKS_NODE_METRICS` | `localhost:9153` | Stacks node metrics endpoint |
| `STACKS_SIGNER_METRICS` | `localhost:30001` | Stacks signer metrics endpoint |
| `BITCOIN_METRICS` | `localhost:9332` | Bitcoin exporter endpoint |
| `HOST_LABEL` | `stacks-node` | Host label for metrics/logs |

### Alloy Configuration

See [`alloy/README.md`](alloy/README.md) for detailed configuration options.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system design
- [Metrics Reference](docs/METRICS.md) - Complete metrics documentation
- [Label Schema](docs/LABELS.md) - Labeling conventions
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Stacks Foundation](https://stacks.org/) for the Stacks blockchain
- [Grafana Labs](https://grafana.com/) for Grafana, Alloy, and Loki
- [VictoriaMetrics](https://victoriametrics.com/) for VictoriaMetrics and VictoriaLogs
