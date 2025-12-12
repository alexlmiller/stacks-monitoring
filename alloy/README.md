# Grafana Alloy Configuration

This directory contains Grafana Alloy configurations for collecting and processing Stacks-related metrics and logs.

## Architecture

```
┌─────────────────────────────────────────┐
│            Node Server                   │
│  (stacks-node, stacks-signer, bitcoin)  │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │          Alloy Agent               │ │
│  │  - Scrapes metrics (:9153, :30001) │ │
│  │  - Collects journal logs           │ │
│  │  - Extracts log levels             │ │
│  └────────────────┬───────────────────┘ │
└───────────────────┼─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Monitoring Hub (optional)        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │          Alloy Hub                 │ │
│  │  - Receives logs from agents       │ │
│  │  - Parses Stacks log format        │ │
│  │  - Extracts fields (tx_id, etc.)   │ │
│  └────────────────┬───────────────────┘ │
└───────────────────┼─────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────┐       ┌──────────────┐
│ Prometheus/  │       │   Loki/      │
│VictoriaMetrics│       │VictoriaLogs  │
└──────────────┘       └──────────────┘
```

## Snippets

Copy-paste ready configurations for integrating into your existing Alloy setup:

| File | Purpose |
|------|---------|
| `snippets/stacks-node-scrape.alloy` | Scrape metrics from Stacks node/signer |
| `snippets/stacks-log-collection.alloy` | Collect logs from journal/files |
| `snippets/stacks-level-extraction.alloy` | Extract log levels (INFO/WARN/ERROR) |
| `snippets/stacks-log-parsing.alloy` | Parse Stacks log format, extract fields |

## Examples

Complete example configurations:

| File | Purpose |
|------|---------|
| `examples/node-vm-complete.alloy` | Full agent config for your node server |
| `examples/monitoring-hub-complete.alloy` | Full hub config (optional, for log parsing) |

## Configuration

### Environment Variables

Most snippets support environment variable substitution:

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOY_HOST_LABEL` | `stacks-node` | Host label for metrics/logs |
| `METRICS_TARGET_URL` | - | Prometheus/VictoriaMetrics remote write URL |
| `LOGS_TARGET_URL` | - | Loki/VictoriaLogs push URL |
| `STACKS_NODE_METRICS` | `127.0.0.1:9153` | Stacks node metrics endpoint |
| `STACKS_SIGNER_METRICS` | `127.0.0.1:30001` | Stacks signer metrics endpoint |
| `BITCOIN_METRICS` | `127.0.0.1:9332` | Bitcoin exporter endpoint |

### Choosing Your Setup

**Simple (Direct):** Node → Prometheus/Loki
- Use `node-vm-complete.alloy` on your node server
- Logs go directly to Loki with basic level extraction
- Good for single-node setups

**Advanced (Hub):** Node → Hub → Storage
- Use `node-vm-complete.alloy` on node server (forward to hub)
- Use `monitoring-hub-complete.alloy` on monitoring server
- Advanced log parsing with field extraction
- Better for multi-node setups or when you want rich labels

## Log Parsing Pipeline

The Stacks log parsing pipeline extracts structured fields from Rust logs:

### Input Format
```
LEVEL [timestamp] [file:line] [context] message, key: value, ...
```

### Example
```
INFO [1765243525.041182] [stackslib/src/net/p2p.rs:2102] [p2p:(20444,20443)] Dropping neighbor!, event id: 532, public key: c0fe420d...
```

### Extracted Labels

| Label | Example | Description |
|-------|---------|-------------|
| `level` | `INFO` | Log level |
| `source_file` | `stackslib/src/net/p2p.rs:2102` | Rust source location |
| `component` | `p2p` | Component name |
| `block_height` | `123456` | Current block height |
| `tx_id` | `0934cadf...` | Transaction hash |
| `block_id` | `fb0a620f...` | Block hash |
| `peer_addr` | `192.168.1.5` | Peer IP address |
| `signer_sig_hash` | `abc123...` | Signature hash |
| `public_key` | `02abc...` | Public key |
| `stackerdb_name` | `signers-0-1` | StackerDB contract |

## Installation

### Install Alloy

```bash
# Download latest release
ALLOY_VERSION="1.12.0"
curl -Lo /tmp/alloy.zip https://github.com/grafana/alloy/releases/download/v${ALLOY_VERSION}/alloy-linux-amd64.zip
unzip /tmp/alloy.zip -d /tmp
sudo mv /tmp/alloy-linux-amd64 /usr/local/bin/alloy
sudo chmod +x /usr/local/bin/alloy

# Create user and directories
sudo useradd -r -s /bin/false alloy
sudo mkdir -p /etc/alloy /var/lib/alloy/data
sudo chown -R alloy:alloy /var/lib/alloy
```

### Deploy Configuration

```bash
# Copy your chosen configuration
sudo cp examples/node-vm-complete.alloy /etc/alloy/config.alloy

# Edit with your settings
sudo vim /etc/alloy/config.alloy

# Install systemd service
sudo cp ../systemd/alloy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alloy
```

### Verify

```bash
# Check status
systemctl status alloy

# View logs
journalctl -u alloy -f

# Access debug UI (if enabled)
curl http://localhost:12345/ready
```
