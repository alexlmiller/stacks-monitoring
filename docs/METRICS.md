# Metrics Reference

This document describes the key metrics available from Stacks node, signer, and Bitcoin services.

## Stacks Node Metrics

Exposed on port `9153` by default.

### Block Height

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_node_stx_block_height` | Gauge | Current Stacks block height |
| `stacks_node_burn_block_height` | Gauge | Current Bitcoin block height (burn chain) |
| `stacks_node_burn_block_timestamp` | Gauge | Unix timestamp of last Bitcoin block |

### Peer Network

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_node_peer_count` | Gauge | Number of connected peers |
| `stacks_node_inbound_peers` | Gauge | Inbound peer connections |
| `stacks_node_outbound_peers` | Gauge | Outbound peer connections |

### Mempool

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_node_mempool_size` | Gauge | Transactions in mempool |
| `stacks_node_mempool_bytes` | Gauge | Mempool size in bytes |

### Performance

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_node_process_time_ms` | Histogram | Block processing time |
| `stacks_node_db_read_time_ms` | Histogram | Database read latency |
| `stacks_node_db_write_time_ms` | Histogram | Database write latency |

## Stacks Signer Metrics

Exposed on port `30001` by default.

### Registration Status

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_signer_is_registered` | Gauge | 1 if signer is registered, 0 otherwise |
| `stacks_signer_reward_cycle` | Gauge | Current reward cycle number |

### Block Responses

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `stacks_signer_block_responses_sent` | Counter | `response_type` | Blocks signed/rejected |

Response types:
- `accepted` - Block was signed
- `rejected` - Block was rejected

### Performance

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_signer_block_response_latencies_histogram` | Histogram | Time to respond to blocks |
| `stacks_signer_round_time_ms` | Histogram | Signing round duration |

### Consensus

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_signer_agreement_state_conflicts` | Counter | State machine conflicts |
| `stacks_signer_naka_proposed_blocks` | Counter | Nakamoto blocks proposed |
| `stacks_signer_naka_signed_blocks` | Counter | Nakamoto blocks signed |

### Health

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_signer_last_tenure_time` | Gauge | Timestamp of last tenure |
| `stacks_signer_current_tenure_height` | Gauge | Current tenure block height |

## Bitcoin Metrics (via Exporter)

Exposed on port `9332` by default (bitcoin_exporter).

### Chain Status

| Metric | Type | Description |
|--------|------|-------------|
| `bitcoin_blocks` | Gauge | Current block height |
| `bitcoin_difficulty` | Gauge | Current mining difficulty |
| `bitcoin_hashrate` | Gauge | Network hash rate |

### Mempool

| Metric | Type | Description |
|--------|------|-------------|
| `bitcoin_mempool_size` | Gauge | Transactions in mempool |
| `bitcoin_mempool_bytes` | Gauge | Mempool size in bytes |
| `bitcoin_mempool_usage` | Gauge | Memory used by mempool |

### Network

| Metric | Type | Description |
|--------|------|-------------|
| `bitcoin_peers` | Gauge | Connected peers |
| `bitcoin_warnings` | Gauge | Network warnings active |

### Verification

| Metric | Type | Description |
|--------|------|-------------|
| `bitcoin_verification_progress` | Gauge | IBD progress (0-1) |
| `bitcoin_size_on_disk` | Gauge | Blockchain size in bytes |

## PoX Exporter Metrics

Exposed on port `9816` by default.

### Cycle Information

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_pox_up` | Gauge | 1 if API reachable, 0 otherwise |
| `stacks_pox_current_cycle` | Gauge | Current PoX cycle number |
| `stacks_pox_next_cycle` | Gauge | Next PoX cycle number |
| `stacks_pox_current_burn_height` | Gauge | Current Bitcoin block height |
| `stacks_pox_blocks_until_prepare_phase` | Gauge | Blocks until prepare phase starts |
| `stacks_pox_blocks_until_reward_phase` | Gauge | Blocks until reward phase starts |
| `stacks_pox_next_prepare_start_block` | Gauge | Block where next prepare phase starts |
| `stacks_pox_next_reward_start_block` | Gauge | Block where next reward phase starts |

### Cycle Parameters

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_pox_cycle_length` | Gauge | Total cycle length (2100 blocks) |
| `stacks_pox_prepare_length` | Gauge | Prepare phase length (100 blocks) |
| `stacks_pox_reward_length` | Gauge | Reward phase length (2000 blocks) |

### Registration Status

| Metric | Type | Description |
|--------|------|-------------|
| `stacks_pox_registered_next_cycle` | Gauge | 1=registered, 0=not registered, -1=not configured |
| `stacks_pox_info` | Gauge | Metadata labels (current_cycle, next_cycle, burn_height) |

The `stacks_pox_registered_next_cycle` metric requires `STACKER_ADDRESSES` to be configured. It checks if any of the specified addresses have STX locked beyond the next cycle's start block.

## Alloy Self-Metrics

Exposed on port `12345` at `/metrics`.

### Targets

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `alloy_component_target_up` | Gauge | `component`, `target` | Target health (1=up) |
| `alloy_component_scrape_duration_seconds` | Histogram | `component` | Scrape latency |

### Log Processing

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `loki_process_entries_total` | Counter | `component` | Log entries processed |
| `loki_write_bytes_total` | Counter | `component` | Bytes sent to Loki |
| `loki_write_sent_entries_total` | Counter | `component` | Entries sent |

## Example Queries

### Stacks Health

```promql
# Current block height
stacks_node_stx_block_height{job="stacks"}

# Blocks per hour
rate(stacks_node_stx_block_height[1h]) * 3600

# Signer registration status
stacks_signer_is_registered{job="stacks"}

# Rejection rate (last 5 minutes)
rate(stacks_signer_block_responses_sent{response_type="rejected"}[5m])
/ rate(stacks_signer_block_responses_sent[5m])
```

### Performance

```promql
# P95 block processing time
histogram_quantile(0.95, rate(stacks_node_process_time_ms_bucket[5m]))

# P95 signer response latency
histogram_quantile(0.95, rate(stacks_signer_block_response_latencies_histogram_bucket[5m]))
```

### Network Health

```promql
# Peer count
stacks_node_peer_count{job="stacks"}

# Bitcoin sync status
bitcoin_verification_progress{job="bitcoin"}

# Time since last Bitcoin block
time() - stacks_node_burn_block_timestamp
```

### Recording Rules

Add these to your Prometheus/VictoriaMetrics for efficiency:

```yaml
groups:
  - name: stacks_recording
    rules:
      # Signer rejection rate
      - record: stacks:signer_rejection_rate:5m
        expr: |
          rate(stacks_signer_block_responses_sent{response_type="rejected"}[5m])
          / rate(stacks_signer_block_responses_sent[5m])

      # Block processing P95
      - record: stacks:block_process_p95:5m
        expr: |
          histogram_quantile(0.95, rate(stacks_node_process_time_ms_bucket[5m]))

      # Signer response P95
      - record: stacks:signer_response_p95:5m
        expr: |
          histogram_quantile(0.95, rate(stacks_signer_block_response_latencies_histogram_bucket[5m]))
```

## Dashboard Variables

The included Grafana dashboard uses these variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `$datasource` | datasource | - | Prometheus/VictoriaMetrics datasource |
| `$logs_datasource` | datasource | - | Loki/VictoriaLogs datasource |
| `$job` | query | `stacks` | Job label filter |
| `$host` | query | `.*` | Host label filter |

## Cardinality Notes

To keep metric cardinality manageable:

1. **Static Labels Only**: Avoid high-cardinality labels (transaction IDs, peer addresses)
2. **Use Recording Rules**: Pre-aggregate frequently-used queries
3. **Limit Histograms**: Keep bucket counts reasonable
4. **Host Label**: Use consistent naming (`stacks-node-1`, not timestamps)

Estimated series per node:
- Stacks node: ~50 series
- Stacks signer: ~30 series
- Bitcoin exporter: ~20 series
- Total: ~100 series per monitored host
