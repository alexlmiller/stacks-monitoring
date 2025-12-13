#!/usr/bin/env python3
"""
Stacks PoX Cycle Exporter - Prometheus metrics for stacking cycle monitoring

Monitors Stacks PoX cycles and exposes metrics for alerting on restack deadlines.

Environment Variables:
  STACKS_NODE_URL   - Stacks node RPC endpoint (default: http://localhost:20443)
  POX_EXPORTER_PORT - Port to expose metrics on (default: 9816)

Metrics exposed:
  stacks_pox_up                        - 1 if Stacks node API is reachable
  stacks_pox_blocks_until_prepare_phase - Blocks until next prepare phase starts
  stacks_pox_blocks_until_reward_phase  - Blocks until next reward phase starts
  stacks_pox_current_cycle              - Current PoX cycle number
  stacks_pox_next_cycle                 - Next PoX cycle number
  stacks_pox_current_burn_height        - Current Bitcoin block height
  stacks_pox_next_prepare_start_block   - Block where next prepare phase starts
  stacks_pox_next_reward_start_block    - Block where next reward phase starts
  stacks_pox_cycle_length               - PoX cycle length in blocks (2100)
  stacks_pox_prepare_length             - Prepare phase length in blocks (100)
  stacks_pox_reward_length              - Reward phase length in blocks (2000)
  stacks_pox_info                       - Metadata labels for filtering
"""

import json
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import URLError, HTTPError

# Configuration from environment variables
STACKS_NODE_URL = os.environ.get("STACKS_NODE_URL", "http://localhost:20443")
LISTEN_PORT = int(os.environ.get("POX_EXPORTER_PORT", "9816"))


def fetch_pox_info():
    """Fetch PoX information from Stacks node API."""
    url = f"{STACKS_NODE_URL}/v2/pox"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except (URLError, HTTPError) as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)


def generate_metrics():
    """Generate Prometheus metrics for PoX cycle information."""
    lines = []

    # Help and type declarations
    lines.append("# HELP stacks_pox_up 1 if Stacks node API is reachable")
    lines.append("# TYPE stacks_pox_up gauge")
    lines.append("# HELP stacks_pox_blocks_until_prepare_phase Blocks until next prepare phase starts")
    lines.append("# TYPE stacks_pox_blocks_until_prepare_phase gauge")
    lines.append("# HELP stacks_pox_blocks_until_reward_phase Blocks until next reward phase starts")
    lines.append("# TYPE stacks_pox_blocks_until_reward_phase gauge")
    lines.append("# HELP stacks_pox_current_cycle Current PoX cycle number")
    lines.append("# TYPE stacks_pox_current_cycle gauge")
    lines.append("# HELP stacks_pox_next_cycle Next PoX cycle number")
    lines.append("# TYPE stacks_pox_next_cycle gauge")
    lines.append("# HELP stacks_pox_current_burn_height Current Bitcoin block height")
    lines.append("# TYPE stacks_pox_current_burn_height gauge")
    lines.append("# HELP stacks_pox_next_prepare_start_block Block number where next prepare phase starts")
    lines.append("# TYPE stacks_pox_next_prepare_start_block gauge")
    lines.append("# HELP stacks_pox_next_reward_start_block Block number where next reward phase starts")
    lines.append("# TYPE stacks_pox_next_reward_start_block gauge")
    lines.append("# HELP stacks_pox_cycle_length PoX cycle length in blocks")
    lines.append("# TYPE stacks_pox_cycle_length gauge")
    lines.append("# HELP stacks_pox_prepare_length Prepare phase length in blocks")
    lines.append("# TYPE stacks_pox_prepare_length gauge")
    lines.append("# HELP stacks_pox_reward_length Reward phase length in blocks")
    lines.append("# TYPE stacks_pox_reward_length gauge")
    lines.append("# HELP stacks_pox_info PoX cycle metadata")
    lines.append("# TYPE stacks_pox_info gauge")

    pox_info, error = fetch_pox_info()

    if error:
        # API unreachable
        lines.append("stacks_pox_up 0")
        return "\n".join(lines) + "\n"

    lines.append("stacks_pox_up 1")

    # Extract current cycle info
    current_cycle = pox_info.get("current_cycle", {})
    current_cycle_id = current_cycle.get("id", 0)
    current_burn_height = pox_info.get("current_burnchain_block_height", 0)

    # Extract next cycle info
    next_cycle = pox_info.get("next_cycle", {})
    next_cycle_id = next_cycle.get("id", 0)
    blocks_until_prepare = next_cycle.get("blocks_until_prepare_phase", -1)
    blocks_until_reward = next_cycle.get("blocks_until_reward_phase", -1)

    # Calculate phase boundary blocks
    next_prepare_start = current_burn_height + blocks_until_prepare if blocks_until_prepare >= 0 else 0
    next_reward_start = current_burn_height + blocks_until_reward if blocks_until_reward >= 0 else 0

    # Get cycle/phase lengths from reward_cycle_length and prepare_cycle_length
    cycle_length = pox_info.get("reward_cycle_length", 2100)
    prepare_length = pox_info.get("prepare_cycle_length", 100)
    reward_length = cycle_length - prepare_length

    # Emit metrics
    lines.append(f"stacks_pox_blocks_until_prepare_phase {blocks_until_prepare}")
    lines.append(f"stacks_pox_blocks_until_reward_phase {blocks_until_reward}")
    lines.append(f"stacks_pox_current_cycle {current_cycle_id}")
    lines.append(f"stacks_pox_next_cycle {next_cycle_id}")
    lines.append(f"stacks_pox_current_burn_height {current_burn_height}")
    lines.append(f"stacks_pox_next_prepare_start_block {next_prepare_start}")
    lines.append(f"stacks_pox_next_reward_start_block {next_reward_start}")
    lines.append(f"stacks_pox_cycle_length {cycle_length}")
    lines.append(f"stacks_pox_prepare_length {prepare_length}")
    lines.append(f"stacks_pox_reward_length {reward_length}")

    # Info metric with labels for dashboard filtering
    info_labels = (
        f'current_cycle="{current_cycle_id}",'
        f'next_cycle="{next_cycle_id}",'
        f'burn_height="{current_burn_height}"'
    )
    lines.append(f"stacks_pox_info{{{info_labels}}} 1")

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            metrics = generate_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(metrics.encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging to avoid noise
        pass


def main():
    server = HTTPServer(("0.0.0.0", LISTEN_PORT), MetricsHandler)
    print(f"Stacks PoX Exporter listening on port {LISTEN_PORT}")
    print(f"Fetching PoX info from {STACKS_NODE_URL}")
    server.serve_forever()


if __name__ == "__main__":
    main()
