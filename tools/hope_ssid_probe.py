#!/usr/bin/env python3
"""Only probes the canonical AAF Google Sheet. Never writes to Google APIs."""

import argparse
import sys

from hope.ssid_gateway import RegistryError, read_live_snapshot


def main() -> int:
    cli = argparse.ArgumentParser(description="HOPE read-only SSID identity proof")
    cli.add_argument("--live", action="store_true", help="requires short-lived OAuth token")
    args = cli.parse_args()
    if not args.live:
        cli.error("Only explicit --live proof is supported; use offline unittest for fixture tests")
    try:
        snapshot = read_live_snapshot()
        snapshot.require("HOPE-DIR-001")
        snapshot.require("HOPE-SSID-READER-001")
    except RegistryError as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    print("LIVE_SHEET_READ_PASS_NOT_RUNTIME_INTEGRATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
