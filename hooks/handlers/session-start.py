#!/usr/bin/env python3
"""Session start hook — checks Syntropic137 API reachability.

Stdlib-only (runs outside any venv). Silent on success,
prints a notification JSON on failure suggesting /syn-setup.
"""

import json
import os
import sys
import urllib.request
import urllib.error

API_URL = os.environ.get("SYN_API_URL", "http://localhost:8000")
HEALTH_ENDPOINT = f"{API_URL}/health"
TIMEOUT_SECONDS = 2


def main() -> int:
    try:
        req = urllib.request.Request(HEALTH_ENDPOINT, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status == 200:
                return 0
    except (urllib.error.URLError, OSError, TimeoutError):
        pass

    notification = {
        "notification": {
            "title": "Syntropic137 API unreachable",
            "message": (
                f"Could not connect to {HEALTH_ENDPOINT}. "
                "Run /syn-setup for guided bootstrap or `just dev` to start the stack."
            ),
            "level": "warning",
        }
    }
    print(json.dumps(notification))
    return 0


if __name__ == "__main__":
    sys.exit(main())
