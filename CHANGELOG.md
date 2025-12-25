# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Alloy: Add 15% sampling for high-volume StackerDB messages (configurable via `STACKERDB_SAMPLING_RATE`)

## [1.0.0] - 2025-12-12

### Added
- Initial release
- Grafana dashboard for Stacks Signer monitoring
- Prometheus alert rules for Stacks Node, Signer, and Bitcoin
- Grafana Alloy snippets for log collection and parsing
- Docker deployment with docker-compose
- Systemd service files for native deployment
- Comprehensive documentation
