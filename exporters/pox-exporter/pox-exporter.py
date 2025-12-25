#!/usr/bin/env python3
"""
Stacks PoX Cycle Exporter - Prometheus metrics for stacking cycle monitoring

Monitors Stacks PoX cycles and exposes metrics for alerting on restack deadlines.

Environment Variables:
  STACKS_NODE_URL     - Stacks node RPC endpoint (default: http://localhost:20443)
                        Used for /v2/pox endpoint to get cycle info
  POX_EXPORTER_PORT   - Port to expose metrics on (default: 9816)
  STACKER_ADDRESSES   - Comma-separated list of STX addresses to monitor for
                        registration status (optional, leave empty to disable)
  STACKER_API_URL     - API endpoint for registration checking (default: https://api.hiro.so)
                        Only used when STACKER_ADDRESSES is configured.
                        Requires an API with /extended/v1/address endpoints
                        (Hiro API or local stacks-blockchain-api)

Metrics exposed:
  stacks_pox_up                         - 1 if Stacks node API is reachable
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
  stacks_pox_registered_next_cycle      - 1 if registered, 0 if not, -1 if not configured
"""

import json
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import URLError, HTTPError

# Configuration from environment variables
STACKS_NODE_URL = os.environ.get("STACKS_NODE_URL", "http://localhost:20443")
LISTEN_PORT = int(os.environ.get("POX_EXPORTER_PORT", "9816"))

# Parse stacker addresses from comma-separated env var
_stacker_env = os.environ.get("STACKER_ADDRESSES", "").strip()
STACKER_ADDRESSES = [addr.strip() for addr in _stacker_env.split(",") if addr.strip()]

# Stacker API URL - only used when STACKER_ADDRESSES is configured
# Defaults to Hiro API since registration checking requires extended API endpoints
# that aren't available on the core Stacks node
STACKER_API_URL = os.environ.get("STACKER_API_URL", "https://api.hiro.so")


def fetch_pox_info():
    """Fetch PoX information from local Stacks node."""
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


def fetch_stacker_info(address):
    """
    Fetch stacking info for a specific address.

    Uses the extended API endpoint which requires Hiro API or a node with
    the stacks-blockchain-api running. This is NOT available on the core
    Stacks node - it requires the stacks-blockchain-api indexer.
    """
    url = f"{STACKER_API_URL}/extended/v1/address/{address}/stx"

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


def check_next_cycle_registration(next_reward_start_block):
    """
    Check if any of the configured stacker addresses are registered for the next cycle.

    A stacker is registered for the next cycle if their unlock_height > next_reward_start_block.
    This means their STX will still be locked when the next cycle starts.

    Returns:
        1  - At least one address is registered for next cycle
        0  - No addresses are registered for next cycle
        -1 - No addresses configured (feature disabled)
    """
    if not STACKER_ADDRESSES:
        return -1  # No addresses configured

    for address in STACKER_ADDRESSES:
        info, error = fetch_stacker_info(address)
        if error:
            continue

        unlock_height = info.get("burnchain_unlock_height", 0)
        locked = info.get("locked", "0")

        # If locked amount > 0 and unlock is after next cycle starts, we're registered
        if int(locked) > 0 and unlock_height > next_reward_start_block:
            return 1

    return 0


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
    lines.append("# HELP stacks_pox_registered_next_cycle 1 if registered for next cycle, 0 if not, -1 if not configured")
    lines.append("# TYPE stacks_pox_registered_next_cycle gauge")

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

    # Check registration status for next cycle
    registered_next_cycle = check_next_cycle_registration(next_reward_start)

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
    lines.append(f"stacks_pox_registered_next_cycle {registered_next_cycle}")

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
    print(f"Fetching PoX info from {STACKS_NODE_URL}/v2/pox")
    if STACKER_ADDRESSES:
        print(f"Monitoring {len(STACKER_ADDRESSES)} stacker address(es) for registration status")
        print(f"Using {STACKER_API_URL} for registration checking (extended API)")
    else:
        print("No STACKER_ADDRESSES configured - registration checking disabled")
    server.serve_forever()


if __name__ == "__main__":
    main()
