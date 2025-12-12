# Docker Deployment

This directory contains Docker Compose configurations for deploying the Stacks monitoring stack.

## Configurations

| File | Purpose |
|------|---------|
| `docker-compose.node.yml` | Alloy agent for your Stacks node server |
| `docker-compose.yml` | Full monitoring stack (Alloy hub + storage) |
| `.env.example` | Environment variable template |

## Quick Start

### Node Agent Only

Deploy on your Stacks node server to collect and forward metrics/logs:

```bash
# Copy and configure environment
cp .env.example .env
vim .env  # Set your monitoring endpoints

# Start Alloy agent
docker-compose -f docker-compose.node.yml up -d

# View logs
docker-compose -f docker-compose.node.yml logs -f
```

### Full Stack (Hub + Storage)

Deploy a complete monitoring stack on a separate server:

```bash
# Copy and configure
cp .env.example .env

# Start everything
docker-compose up -d

# Access Grafana
open http://localhost:3000
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST_LABEL` | `stacks-node` | Host label for metrics/logs |
| `METRICS_TARGET_URL` | - | Prometheus/VictoriaMetrics remote write URL |
| `LOGS_TARGET_URL` | - | Loki/VictoriaLogs push URL |
| `STACKS_NODE_METRICS` | `host.docker.internal:9153` | Stacks node metrics endpoint |
| `STACKS_SIGNER_METRICS` | `host.docker.internal:30001` | Signer metrics endpoint |
| `BITCOIN_METRICS` | `host.docker.internal:9332` | Bitcoin exporter endpoint |

### Accessing Host Services

The default configuration uses `host.docker.internal` to access services running on the host machine (Stacks node, signer, Bitcoin).

**On Linux**, you may need to add the following to your Docker Compose:

```yaml
services:
  alloy:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Or update the metrics endpoints to use the host's IP address directly.

## Volumes

### Node Agent

| Volume | Purpose |
|--------|---------|
| `/etc/alloy` | Alloy configuration |
| `/var/lib/alloy` | Alloy data directory |
| `/var/log` | Host logs (for file-based log collection) |
| `/run/systemd/journal` | Journald socket (for journal log collection) |

### Full Stack

| Volume | Purpose |
|--------|---------|
| `prometheus_data` | Prometheus TSDB data |
| `victorialogs_data` | VictoriaLogs storage |
| `grafana_data` | Grafana SQLite database and plugins |

## Network

All services communicate on the `stacks-monitoring` bridge network.

## Resource Limits

Default resource limits in docker-compose files:

| Service | Memory | CPU |
|---------|--------|-----|
| Alloy | 512MB | 0.5 |
| Prometheus | 2GB | 1.0 |
| VictoriaLogs | 1GB | 0.5 |
| Grafana | 512MB | 0.5 |

Adjust based on your log/metric volume.

## Troubleshooting

### Alloy can't reach host services

```bash
# Check connectivity from container
docker-compose -f docker-compose.node.yml exec alloy \
  wget -qO- http://host.docker.internal:9153/metrics

# On Linux, add extra_hosts or use host network
docker-compose -f docker-compose.node.yml up -d --network host
```

### Logs not appearing

```bash
# Check Alloy logs
docker-compose -f docker-compose.node.yml logs alloy

# Verify journal access
docker-compose -f docker-compose.node.yml exec alloy \
  ls -la /run/systemd/journal/
```

### High memory usage

Adjust log retention and sampling rates in the Alloy configuration, or increase the container memory limits.
