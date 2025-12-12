# Systemd Deployment

Deploy Grafana Alloy as a systemd service for collecting Stacks metrics and logs.

## Prerequisites

1. **Install Grafana Alloy**

   ```bash
   # Debian/Ubuntu
   wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
   echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
   sudo apt update
   sudo apt install alloy

   # Or download binary directly
   curl -LO https://github.com/grafana/alloy/releases/latest/download/alloy-linux-amd64.zip
   unzip alloy-linux-amd64.zip
   sudo mv alloy-linux-amd64 /usr/local/bin/alloy
   sudo chmod +x /usr/local/bin/alloy
   ```

2. **Create alloy user and directories**

   ```bash
   sudo useradd --system --no-create-home --shell /bin/false alloy
   sudo mkdir -p /etc/alloy /var/lib/alloy/data
   sudo chown -R alloy:alloy /var/lib/alloy
   ```

## Installation

### 1. Copy configuration files

```bash
# Copy Alloy configuration
sudo cp ../alloy/examples/node-vm-complete.alloy /etc/alloy/config.alloy

# Copy environment file
sudo cp alloy.env /etc/default/alloy
sudo chmod 600 /etc/default/alloy

# Edit environment for your setup
sudo vim /etc/default/alloy
```

### 2. Install systemd service

```bash
# Copy service file
sudo cp alloy.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable --now alloy

# Check status
sudo systemctl status alloy
```

## Configuration

### Environment Variables

Edit `/etc/default/alloy`:

| Variable | Description | Example |
|----------|-------------|---------|
| `ALLOY_CONFIG` | Path to Alloy config | `/etc/alloy/config.alloy` |
| `HOST_LABEL` | Host identifier for metrics/logs | `stacks-node-1` |
| `METRICS_TARGET_URL` | Prometheus/VictoriaMetrics endpoint | `http://monitoring:8428/api/v1/write` |
| `LOGS_TARGET_URL` | Loki/VictoriaLogs endpoint | `http://monitoring:3100/loki/api/v1/push` |
| `STACKS_NODE_METRICS` | Stacks node metrics endpoint | `localhost:9153` |
| `STACKS_SIGNER_METRICS` | Signer metrics endpoint | `localhost:30001` |
| `BITCOIN_METRICS` | Bitcoin exporter endpoint | `localhost:9332` |

### Alloy Configuration

The configuration file at `/etc/alloy/config.alloy` uses environment variables:

```alloy
// Example: using environment variables
prometheus.remote_write "default" {
  endpoint {
    url = env("METRICS_TARGET_URL")
  }
}
```

See `../alloy/examples/` for complete configuration examples.

## Operations

### View logs

```bash
# Follow logs
journalctl -u alloy -f

# Last 100 lines
journalctl -u alloy -n 100

# Filter by severity
journalctl -u alloy -p err
```

### Reload configuration

```bash
# Reload without restart
sudo systemctl reload alloy

# Or full restart
sudo systemctl restart alloy
```

### Check status

```bash
# Service status
sudo systemctl status alloy

# Alloy health endpoint
curl -s http://localhost:12345/ready

# Alloy metrics
curl -s http://localhost:12345/metrics | head
```

### Debug UI

Access the Alloy debug UI at `http://localhost:12345`:
- Component graph
- Configuration status
- Targets and scrape status
- Log pipeline visualization

## Security Considerations

The provided service file includes security hardening:

- `NoNewPrivileges=true` - Prevents privilege escalation
- `ProtectSystem=strict` - Read-only filesystem except allowed paths
- `ProtectHome=true` - No access to home directories
- `PrivateTmp=true` - Isolated /tmp
- `PrivateDevices=true` - No access to devices

### Journal Access

To read systemd journal logs, Alloy needs journal access:

```bash
# Add alloy user to systemd-journal group
sudo usermod -aG systemd-journal alloy
sudo systemctl restart alloy
```

### File Log Access

For file-based log collection from `/var/log`:

```bash
# Alloy needs read access to log files
sudo setfacl -R -m u:alloy:rx /var/log/stacks
```

## Troubleshooting

### Service won't start

```bash
# Check for configuration errors
/usr/local/bin/alloy run --config.file=/etc/alloy/config.alloy --dry-run

# Check permissions
ls -la /etc/alloy/config.alloy
ls -la /var/lib/alloy/
```

### Can't scrape local services

Ensure Stacks services are listening on the expected ports:

```bash
# Check Stacks node
curl -s http://localhost:9153/metrics | head

# Check Signer
curl -s http://localhost:30001/metrics | head

# Check Bitcoin exporter
curl -s http://localhost:9332/metrics | head
```

### Logs not appearing

1. Check Alloy logs for errors:
   ```bash
   journalctl -u alloy -p err --since "10 minutes ago"
   ```

2. Verify remote endpoint connectivity:
   ```bash
   curl -s http://monitoring-hub:9428/health
   ```

3. Check Alloy component status:
   ```bash
   curl -s http://localhost:12345/api/v0/web/components | jq .
   ```

## Uninstall

```bash
sudo systemctl stop alloy
sudo systemctl disable alloy
sudo rm /etc/systemd/system/alloy.service
sudo systemctl daemon-reload
sudo rm -rf /etc/alloy /var/lib/alloy
sudo userdel alloy
```
