# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-27

### Added
- Optional VictoriaLogs Grafana alert provisioning example for Stacks node, signer, and Bitcoin log-silence alerts.
- Optional VictoriaLogs tenure-conflict alert for repeated WARN-level signer tenure messages.
- Log-based alerting documentation with VictoriaLogs provisioning notes and Loki equivalent queries.
- Dashboard `To Next Cycle` stat panel backed by the optional PoX exporter.
- `POX_EXPORTER_LISTEN_ADDRESS` support for the PoX exporter. Docker examples bind to `0.0.0.0`; systemd examples bind to `127.0.0.1`.

### Fixed
- Removed a stale Grafana alert-list `recovering` state filter that Grafana 10.4 rejects during dashboard rendering.
- Prometheus alert rules no longer include log-query syntax that Prometheus cannot evaluate.
- Updated dashboard, alerts, and docs to use current local metric names:
  - `stacks_node_stacks_tip_height`
  - `stacks_node_neighbors_inbound`
  - `stacks_node_neighbors_outbound`
  - `stacks_signer_current_reward_cycle`
  - `bitcoin_conn_in`
  - `bitcoin_conn_out`

### Changed
- Dashboard `Peer Count` now shows total inbound and outbound Stacks peer connections.
- Public dashboard and docs now consistently default to `job="stacks"`.
- PoX alert labels now use `service="stacks-pox"` while keeping scrape detection compatible with older `service="pox-exporter"` targets.
- Documentation now explicitly states that local-vs-Hiro block-height comparison metrics, alerts, and panels are intentionally out of scope.

### Removed
- Removed the stale `BitcoinBlockStall` alert, which did not provide useful signal.
- Removed obsolete Grafana JSON alert provisioning file in favor of YAML provisioning.
- Removed the documented `STACKERDB_SAMPLING_RATE` env override because Alloy's `env()` values are strings and do not type-check as numeric `stage.sampling.rate` values. Edit the sampling rate literal in the Alloy example instead.

### Migration Notes
- If your dashboard data uses a non-default job label, update dashboard queries and variables from `job="stacks"` to your label. Older examples also matched `job="crypto"`; 1.2.0 defaults to `stacks` only.
- If you previously set `STACKERDB_SAMPLING_RATE`, edit the `stage.sampling.rate` literal in your Alloy config instead.

## [1.1.0] - 2025-12-25

### Added
- Block production early warning alerts (StacksBlockProductionDegraded, StacksBlockProductionIssues, StacksBlockStall)
- Signer network indicator alerts (StacksSignerHighRejectionCount, StacksSignerHighProposalRate)
- Bitcoin low peers alert (BitcoinLowPeers)
- PoX exporter registration checking with STACKER_ADDRESSES env var
- STACKER_API_URL for extended API access (defaults to Hiro API, only used when STACKER_ADDRESSES is set)
- Grafana alerting YAML provisioning format (stacks-alerts.yaml)

### Changed
- Restack alerts now incorporate registration status (only fire if not registered)
- Added fallback alert for when registration checking is disabled
- Dashboard: Split signer warnings into Timeouts (orange), Invalid (red), and Other WARNs (yellow) for better visibility
- Dashboard: Split node warnings into Network Errors (orange) and Chain Errors (red)
- Alloy: Add 15% sampling for high-volume StackerDB messages. Note: the originally documented `STACKERDB_SAMPLING_RATE` env override was removed in 1.2.0 because it did not type-check correctly in Alloy.

## [1.0.0] - 2025-12-12

### Added
- Initial release
- Grafana dashboard for Stacks Signer monitoring
- Prometheus alert rules for Stacks Node, Signer, and Bitcoin
- Grafana Alloy snippets for log collection and parsing
- Docker deployment with docker-compose
- Systemd service files for native deployment
- Comprehensive documentation
