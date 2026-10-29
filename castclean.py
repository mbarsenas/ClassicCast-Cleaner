#!/usr/bin/env python3
"""Read-only inspection and experimental telemetry preference controls for classic Chromecast."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

KNOWN_PATHS = (
    "/setup/eureka_info",
    "/setup/configured_networks",
    "/setup/supported_locales",
    "/setup/supported_timezones",
    "/setup/supported_languages",
    "/setup/supported_time_formats",
    "/setup/set_eureka_info",
)
BACKUP_DIR = Path("backups")


class CastAPIError(RuntimeError):
    pass


class ChromecastAPI:
    def __init__(self, host: str, port: int = 8443, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base = f"https://{host}:{port}"
        # Classic Chromecast setup endpoints may use a self-signed certificate.
        self.ssl_context = ssl._create_unverified_context()

    def request(self, path: str, method: str = "GET",
                payload: dict[str, Any] | None = None) -> tuple[int, str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        # Protected setup endpoints may require the device-local authorization token.
        # Keep it in an environment variable so it is not hard-coded or logged.
        token = os.environ.get("CAST_LOCAL_AUTHORIZATION_TOKEN")
        if token:
            headers["cast-local-authorization-token"] = token
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self.ssl_context) as response:
                raw = response.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw) if raw else None
                except json.JSONDecodeError:
                    parsed = raw
                return response.status, raw, parsed
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return exc.code, raw, raw
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CastAPIError(str(exc)) from exc

    def info(self) -> dict[str, Any]:
        status, raw, parsed = self.request("/setup/eureka_info")
        if status != 200 or not isinstance(parsed, dict):
            raise CastAPIError(f"eureka_info returned HTTP {status}: {raw[:200]}")
        return parsed


def safe_info(info: dict[str, Any]) -> dict[str, Any]:
    """Only print fields useful for debugging; omit IDs, addresses and public keys."""
    keys = (
        "name", "build_version", "cast_build_revision", "connected",
        "ethernet_connected", "locale", "opt_in", "setup_state",
        "has_update", "time_format", "timezone", "wpa_configured",
    )
    return {key: info[key] for key in keys if key in info}


def save_backup(host: str, info: dict[str, Any]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    data = {
        "created_at": dt.datetime.now().astimezone().isoformat(),
        "host": host,
        "firmware": info.get("cast_build_revision"),
        "name": info.get("name"),
        "locale": info.get("locale"),
        "opt_in": info.get("opt_in", {}),
        "timezone": info.get("timezone"),
        "time_format": info.get("time_format"),
        "note": "Private local backup. Do not commit this file to a public repository.",
    }
    path = BACKUP_DIR / f"settings-{stamp}.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def cmd_inspect(api: ChromecastAPI) -> int:
    info = api.info()
    print(json.dumps(safe_info(info), indent=2))
    print("\nSensitive device identifiers were omitted.")
    return 0


def cmd_probe(api: ChromecastAPI) -> int:
    print(f"GET-only probe of known setup paths at {api.host}:{api.port}")
    for path in KNOWN_PATHS:
        try:
            status, body, parsed = api.request(path)
            detail = ""
            if isinstance(parsed, dict):
                detail = " JSON keys: " + ", ".join(list(parsed)[:8])
            elif isinstance(parsed, list):
                detail = f" JSON list ({len(parsed)} items)"
            elif body:
                detail = " body: " + repr(body[:70])
            print(f"{status:3} {path}{detail}")
        except CastAPIError as exc:
            print(f"ERROR {path}: {exc}")
    print("This probe does not modify the device.")
    return 0


def cmd_backup(api: ChromecastAPI, host: str) -> int:
    info = api.info()
    path = save_backup(host, info)
    print(f"Backup saved locally: {path}")
    print(json.dumps(safe_info(info), indent=2))
    return 0


def cmd_telemetry_off(api: ChromecastAPI, host: str, apply: bool) -> int:
    info = api.info()
    print("Authorization token configured:", bool(os.environ.get("CAST_LOCAL_AUTHORIZATION_TOKEN")))
    print("Current opt-in settings:")
    print(json.dumps(info.get("opt_in", {}), indent=2))
    if not apply:
        print("\nDRY RUN: no changes made. Add --apply to attempt stats=false and crash=false.")
        return 0

    backup = save_backup(host, info)
    print(f"Saved pre-change backup: {backup}")
    payload = {"opt_in": {"stats": False, "crash": False}}
    status, body, _ = api.request("/setup/set_eureka_info", method="POST", payload=payload)
    print(f"POST /setup/set_eureka_info -> HTTP {status}")
    if body:
        print("Response:", body[:250])
    if not 200 <= status < 300:
        print("Change not confirmed. Backup retained.")
        return 2

    after = api.info()
    values = after.get("opt_in", {})
    print("Read-back opt-in settings:")
    print(json.dumps(values, indent=2))
    if values.get("stats") is False and values.get("crash") is False:
        print("VERIFIED: stats and crash preferences read back as false.")
        return 0
    print("WARNING: response was successful, but requested settings did not verify.")
    print(f"Backup retained: {backup}")
    return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="Classic Chromecast setup API inspection tool")
    parser.add_argument("--host", required=True, help="Chromecast IP address or hostname")
    parser.add_argument("--port", type=int, choices=(8008, 8443), default=8443)
    parser.add_argument("--timeout", type=float, default=5.0)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("inspect", help="Read non-sensitive device information")
    subs.add_parser("probe", help="GET known paths only")
    subs.add_parser("backup", help="Save current settings locally")
    telemetry = subs.add_parser("telemetry-off", help="Dry-run or attempt telemetry opt-out")
    telemetry.add_argument("--apply", action="store_true", help="Submit the experimental preference change")
    args = parser.parse_args()

    api = ChromecastAPI(args.host, args.port, args.timeout)
    try:
        if args.command == "inspect":
            return cmd_inspect(api)
        if args.command == "probe":
            return cmd_probe(api)
        if args.command == "backup":
            return cmd_backup(api, args.host)
        if args.command == "telemetry-off":
            return cmd_telemetry_off(api, args.host, args.apply)
    except CastAPIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Check the host, port, LAN connection, and whether the Chromecast is awake.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
