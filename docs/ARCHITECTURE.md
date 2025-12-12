# Architecture

This document describes the architecture of the Stacks monitoring stack.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STACKS NODE SERVER                                │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │ Stacks Node │  │   Signer    │  │   Bitcoin   │                          │
│  │   :9153     │  │   :30001    │  │   :9332     │                          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                          │
│         │                │                │                                  │
│         │  ┌─────────────┴────────────────┘                                  │
│         │  │                                                                 │
│         ▼  ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │                    GRAFANA ALLOY (Agent)                      │           │
│  │                                                               │           │
│  │  ┌──────────────────┐      ┌──────────────────┐              │           │
│  │  │ prometheus.scrape │      │ loki.source.*    │              │           │
│  │  │  - stacks-node   │      │  - journal       │              │           │
│  │  │  - stacks-signer │      │  - file          │              │           │
│  │  │  - bitcoin       │      │                  │              │           │
│  │  └────────┬─────────┘      └────────┬─────────┘              │           │
│  │           │                         │                         │           │
│  │           │                         ▼                         │           │
│  │           │               ┌──────────────────┐               │           │
│  │           │               │  loki.process    │               │           │
│  │           │               │  (level extract) │               │           │
│  │           │               └────────┬─────────┘               │           │
│  │           │                        │                          │           │
│  │           ▼                        ▼                          │           │
│  │  ┌──────────────────┐    ┌──────────────────┐               │           │
│  │  │prometheus.remote_│    │   loki.write     │               │           │
│  │  │     write        │    │                  │               │           │
│  │  └────────┬─────────┘    └────────┬─────────┘               │           │
│  │           │                       │                          │           │
│  └───────────┼───────────────────────┼──────────────────────────┘           │
│              │                       │                                       │
└──────────────┼───────────────────────┼───────────────────────────────────────┘
               │                       │
               │     NETWORK           │
               │                       │
               ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONITORING HUB SERVER                                │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │                    GRAFANA ALLOY (Hub)                             │      │
│  │                                                                    │      │
│  │  ┌────────────────────┐    ┌────────────────────┐                 │      │
│  │  │ prometheus.receive │    │   loki.source.api  │                 │      │
│  │  │      :9091         │    │       :3500        │                 │      │
│  │  └─────────┬──────────┘    └─────────┬──────────┘                 │      │
│  │            │                         │                             │      │
│  │            │                         ▼                             │      │
│  │            │               ┌─────────────────────┐                │      │
│  │            │               │    loki.process     │                │      │
│  │            │               │  (stacks parsing)   │                │      │
│  │            │               │  - regex extraction │                │      │
│  │            │               │  - field parsing    │                │      │
│  │            │               │  - level mapping    │                │      │
│  │            │               └─────────┬───────────┘                │      │
│  │            │                         │                             │      │
│  │            ▼                         ▼                             │      │
│  │   ┌────────────────────┐    ┌────────────────────┐               │      │
│  │   │prometheus.remote_  │    │    loki.write      │               │      │
│  │   │      write         │    │                    │               │      │
│  │   └─────────┬──────────┘    └─────────┬──────────┘               │      │
│  │             │                         │                           │      │
│  └─────────────┼─────────────────────────┼───────────────────────────┘      │
│                │                         │                                   │
│                ▼                         ▼                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │   VictoriaMetrics /     │  │   VictoriaLogs /        │                   │
│  │   Prometheus            │  │   Loki                  │                   │
│  │        :8428            │  │        :9428            │                   │
│  └───────────┬─────────────┘  └───────────┬─────────────┘                   │
│              │                            │                                  │
│              └─────────────┬──────────────┘                                  │
│                            │                                                 │
│                            ▼                                                 │
│              ┌─────────────────────────┐                                    │
│              │        GRAFANA          │                                    │
│              │         :3000           │                                    │
│              │  - Dashboards           │                                    │
│              │  - Alerts               │                                    │
│              │  - Explore              │                                    │
│              └─────────────────────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### Stacks Node Server

Services running on your Stacks node machine:

| Service | Port | Description |
|---------|------|-------------|
| Stacks Node | 9153 | Stacks blockchain node metrics |
| Stacks Signer | 30001 | Signer service metrics |
| Bitcoin Exporter | 9332 | Bitcoin node metrics (via exporter) |
| Alloy Agent | 12345 | Telemetry collector (debug UI) |

### Monitoring Hub Server

Centralized monitoring infrastructure:

| Service | Port | Description |
|---------|------|-------------|
| Alloy Hub | 12345 | Debug UI |
| Alloy Hub | 3500 | Loki API receiver (logs) |
| Alloy Hub | 9091 | Prometheus receiver (metrics) |
| VictoriaMetrics | 8428 | Metrics storage & query |
| VictoriaLogs | 9428 | Log storage & query |
| Grafana | 3000 | Visualization & alerting |

## Data Flow

### Metrics Pipeline

```
Stacks Node (:9153) ─┐
Signer (:30001) ─────┼─► Alloy scrape ─► remote_write ─► VictoriaMetrics ─► Grafana
Bitcoin (:9332) ─────┘
```

1. **Collection**: Alloy scrapes Prometheus endpoints every 15s
2. **Labeling**: Adds `host`, `job`, `service` labels
3. **Transport**: Remote write to VictoriaMetrics/Prometheus
4. **Storage**: Time-series database with retention
5. **Query**: PromQL queries from Grafana

### Logs Pipeline

```
Journal (systemd) ─┐
Signer file logs ──┼─► Alloy source ─► process ─► loki.write ─► VictoriaLogs ─► Grafana
                   │     (collect)     (parse)
```

1. **Collection**: Alloy reads journal and/or log files
2. **Level Extraction**: Extracts INFO/WARN/ERROR from log content
3. **Transport**: Push to Loki/VictoriaLogs endpoint
4. **Hub Processing**: Parses Stacks log format, extracts fields
5. **Storage**: Log database with retention
6. **Query**: LogQL queries from Grafana

## Log Processing Pipeline

The Stacks log format is parsed in multiple stages:

### Stage 1: Level Extraction (Node Agent)

```
Input:  INFO [1234567890.123] [src/main.rs:42] [context] message
Output: Labels: level=info
```

### Stage 2: Stacks Parsing (Hub)

```
Input:  INFO [1234567890.123] [src/chainstate/coordinator/mod.rs:1234] [tenure_id:abc] Processing block, height: 12345
Output:
  - Labels: level=info, source_file=src/chainstate/coordinator/mod.rs
  - Extracted: block_height=12345, component=coordinator
```

## Deployment Options

### Option A: Single Server

All components on one machine (development/small scale):

```
┌─────────────────────────────────────────┐
│           Single Server                  │
│                                          │
│  Stacks Node + Signer + Bitcoin          │
│              │                           │
│              ▼                           │
│  Alloy (combined agent + hub)            │
│              │                           │
│              ▼                           │
│  VictoriaMetrics + VictoriaLogs          │
│              │                           │
│              ▼                           │
│          Grafana                         │
└─────────────────────────────────────────┘
```

### Option B: Separated (Recommended)

Dedicated monitoring infrastructure:

```
┌──────────────────┐      ┌──────────────────┐
│   Node Server    │      │  Monitoring Hub  │
│                  │      │                  │
│  Stacks + Signer │─────►│  Alloy Hub       │
│  + Alloy Agent   │      │  VM/VL + Grafana │
└──────────────────┘      └──────────────────┘
```

### Option C: Multi-Node

Multiple Stacks nodes reporting to central hub:

```
┌────────────────┐
│  Node Server 1 │────┐
└────────────────┘    │
                      │    ┌──────────────────┐
┌────────────────┐    ├───►│  Monitoring Hub  │
│  Node Server 2 │────┤    └──────────────────┘
└────────────────┘    │
                      │
┌────────────────┐    │
│  Node Server N │────┘
└────────────────┘
```

## Network Requirements

### Node Agent → Monitoring Hub

| Source | Destination | Port | Protocol |
|--------|-------------|------|----------|
| Alloy Agent | Alloy Hub (metrics) | 9091 | HTTP |
| Alloy Agent | Alloy Hub (logs) | 3500 | HTTP |

### Internal (Monitoring Hub)

| Source | Destination | Port | Protocol |
|--------|-------------|------|----------|
| Alloy Hub | VictoriaMetrics | 8428 | HTTP |
| Alloy Hub | VictoriaLogs | 9428 | HTTP |
| Grafana | VictoriaMetrics | 8428 | HTTP |
| Grafana | VictoriaLogs | 9428 | HTTP |

## Storage Requirements

### Metrics (VictoriaMetrics)

- ~50-100 active time series per Stacks node
- ~1KB per series per day
- Estimate: ~100MB/day per node with 15s scrape interval

### Logs (VictoriaLogs)

- Highly variable based on log verbosity
- Stacks node: 10-100MB/day typical
- Signer: 50-500MB/day (verbose during signing rounds)
- Apply sampling for high-volume logs

## High Availability

For production deployments consider:

1. **VictoriaMetrics Cluster**: Multi-node setup with replication
2. **VictoriaLogs Cluster**: Distributed log storage
3. **Multiple Alloy Agents**: Per-node redundancy
4. **Grafana HA**: Multiple instances with shared database
