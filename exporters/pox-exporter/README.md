# Stacks PoX Cycle Exporter

Prometheus exporter for monitoring Stacks Proof of Transfer (PoX) cycle status. Provides metrics for alerting on stacking deadlines and tracking cycle progression.

## Overview

The PoX exporter queries your Stacks node's `/v2/pox` endpoint and exposes metrics about:
- Current and next PoX cycle numbers
- Blocks remaining until prepare and reward phases
- Bitcoin burn block height
- Cycle timing parameters

These metrics enable alerting on restack deadlines so you don't miss a stacking cycle.

## Quick Start

### Docker (Recommended)

```bash
# Point to your Stacks node
export STACKS_NODE_URL=http://stacks-node:20443

docker compose up -d
```

### Systemd

```bash
# Copy files
sudo cp pox-exporter.py /opt/pox-exporter/
sudo cp systemd/pox-exporter.service /etc/systemd/system/
sudo cp systemd/pox-exporter.env /etc/default/pox-exporter

# Edit configuration
sudo vim /etc/default/pox-exporter

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now pox-exporter
```

### Manual

```bash
export STACKS_NODE_URL=http://localhost:20443
export POX_EXPORTER_PORT=9816

python3 pox-exporter.py
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `STACKS_NODE_URL` | `http://localhost:20443` | Stacks node RPC endpoint (for `/v2/pox`) |
| `POX_EXPORTER_PORT` | `9816` | Port to expose metrics on |
| `STACKER_ADDRESSES` | (empty) | Comma-separated STX addresses to monitor for registration |
| `STACKER_API_URL` | `https://api.hiro.so` | API for registration checking (only used when STACKER_ADDRESSES is set) |

### Registration Checking

When `STACKER_ADDRESSES` is configured, the exporter checks if any of the specified addresses are registered for the next stacking cycle. This enables smarter alerting - restack alerts will only fire if you're not already registered.

```bash
# Basic setup - PoX info from local node only
export STACKS_NODE_URL=http://localhost:20443

# Enable registration checking (uses Hiro API by default)
export STACKER_ADDRESSES=SP1ABC...,SP2DEF...

# Or use your own stacks-blockchain-api instance
export STACKER_API_URL=http://localhost:3999
```

**Note:** Registration checking requires the extended API endpoints (`/extended/v1/address/...`) which are NOT available on the core Stacks node. You need either:
- The public Hiro API (default)
- Your own [stacks-blockchain-api](https://github.com/hirosystems/stacks-blockchain-api) instance

The `stacks_pox_registered_next_cycle` metric will return:
- `1` - At least one address is registered for the next cycle
- `0` - No addresses are registered (alert should fire)
- `-1` - No addresses configured (feature disabled)

## Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_pox_up` | Gauge | 1 if Stacks node API is reachable |
| `stacks_pox_blocks_until_prepare_phase` | Gauge | Blocks until next prepare phase starts |
| `stacks_pox_blocks_until_reward_phase` | Gauge | Blocks until next reward phase starts |
| `stacks_pox_current_cycle` | Gauge | Current PoX cycle number |
| `stacks_pox_next_cycle` | Gauge | Next PoX cycle number |
| `stacks_pox_current_burn_height` | Gauge | Current Bitcoin block height |
| `stacks_pox_next_prepare_start_block` | Gauge | Block where next prepare phase starts |
| `stacks_pox_next_reward_start_block` | Gauge | Block where next reward phase starts |
| `stacks_pox_cycle_length` | Gauge | PoX cycle length in blocks (2100) |
| `stacks_pox_prepare_length` | Gauge | Prepare phase length in blocks (100) |
| `stacks_pox_reward_length` | Gauge | Reward phase length in blocks (2000) |
| `stacks_pox_info` | Gauge | Metadata labels for filtering |
| `stacks_pox_registered_next_cycle` | Gauge | 1 if registered, 0 if not, -1 if not configured |

## Endpoints

| Path | Description |
|------|-------------|
| `/metrics` | Prometheus metrics |
| `/health` | Health check (returns `{"status": "ok"}`) |

## Example Metrics Output

```
# HELP stacks_pox_up 1 if Stacks node API is reachable
# TYPE stacks_pox_up gauge
stacks_pox_up 1
# HELP stacks_pox_blocks_until_prepare_phase Blocks until next prepare phase starts
# TYPE stacks_pox_blocks_until_prepare_phase gauge
stacks_pox_blocks_until_prepare_phase 847
# HELP stacks_pox_current_cycle Current PoX cycle number
# TYPE stacks_pox_current_cycle gauge
stacks_pox_current_cycle 96
# HELP stacks_pox_next_cycle Next PoX cycle number
# TYPE stacks_pox_next_cycle gauge
stacks_pox_next_cycle 97
```

## Alloy Integration

See [alloy/snippets/pox-exporter-scrape.alloy](../../alloy/snippets/pox-exporter-scrape.alloy) for a ready-to-use scrape configuration.

## Alert Rules

See [prometheus/alerts/pox.rules.yml](../../prometheus/alerts/pox.rules.yml) for recommended alert rules:

| Alert | Severity | Trigger |
|-------|----------|---------|
| `StacksPoXExporterDown` | Warning | Exporter unreachable for 5m |
| `StacksPoXApiUnreachable` | Warning | Cannot reach Stacks node API |
| `StacksRestackReminder` | Warning | <720 blocks AND not registered for next cycle |
| `StacksRestackUrgent` | Critical | <144 blocks AND not registered for next cycle |
| `StacksRestackReminderNoCheck` | Info | <720 blocks (when registration check disabled) |

When `STACKER_ADDRESSES` is configured, the restack alerts will automatically stop firing once you're registered for the next cycle.

## PoX Cycle Timing

- **Cycle Length**: 2100 Bitcoin blocks (~2 weeks)
- **Prepare Phase**: 100 blocks at the end of each cycle
- **Reward Phase**: 2000 blocks (main stacking period)

You must restack before the prepare phase begins to participate in the next cycle.

## Requirements

- Python 3.8+ (standard library only, no pip dependencies)
- Access to a Stacks node RPC endpoint
