# ClassicCast Cleaner

A Windows-friendly research toolkit for **classic Chromecast / Eureka Cast firmware**.

This is not an Android TV debloater. Classic Chromecast firmware does not expose Android's normal ADB package manager, so Android TV commands such as `adb shell pm disable-user` do not apply.

## What it does today

- Read device information from `/setup/eureka_info`.
- Probe selected setup API paths using GET requests only.
- Save a local settings backup while omitting device public keys and persistent identifiers.
- Offer an opt-in attempt to disable Chromecast-level `stats` and `crash` reporting flags using `POST /setup/set_eureka_info`.
- Re-read settings to verify the result rather than trusting the HTTP response.

## Limitations

- It does **not** uninstall firmware components or install a replacement launcher.
- Chromecast-level telemetry preferences are not the same as ads shown inside YouTube or other streaming apps.
- DNS filtering is not implemented yet. Any future blocklist should be based on observed traffic and include rollback instructions.
- HTTPS requests accept the device's self-signed certificate. Use only on a trusted local network and verify the target IP.
- Write operations are opt-in and require `--apply`.

## Requirements

- Windows 10/11 and Python 3.10+ (standard library only).
- PC and Chromecast on the same LAN.

## Quick start (PowerShell)

```powershell
python .\\castclean.py --host 192.168.1.208 inspect
python .\\castclean.py --host 192.168.1.208 probe
python .\\castclean.py --host 192.168.1.208 backup
```

The IP above is only an example from development testing; use your Chromecast's current IP.

### Telemetry preferences

First run a dry run:

```powershell
python .\\castclean.py --host 192.168.1.208 telemetry-off
```

Review the displayed current settings. If you choose to test the change on your own device, use:

```powershell
python .\\castclean.py --host 192.168.1.208 telemetry-off --apply
```

The tool saves a local backup first, submits `stats=false` and `crash=false`, and reads the device information again. This write path is experimental and must be verified on each firmware version; a successful HTTP status alone is not proof the settings persisted.

If the write returns `HTTP 401`, the device requires a local authorization token for protected setup endpoints. The tool supports the `CAST_LOCAL_AUTHORIZATION_TOKEN` environment variable and sends it in the `cast-local-authorization-token` header. The token is not bundled with this project, printed, or saved to disk. Obtain it only through a legitimate Google Home app/session you control; do not paste it into an issue or commit it to Git. Example PowerShell prompt that avoids echoing the token:

```powershell
$secure = Read-Host "Local Chromecast authorization token" -AsSecureString
$env:CAST_LOCAL_AUTHORIZATION_TOKEN = [System.Net.NetworkCredential]::new("", $secure).Password
python .\\castclean.py --host 192.168.1.208 telemetry-off --apply
Remove-Item Env:CAST_LOCAL_AUTHORIZATION_TOKEN
```

Do not keep retrying writes without a valid token. If you do not have a legitimate way to obtain one, leave the setting unchanged and use the project for read-only research.

## Development

```powershell
python -m unittest discover -s tests -v
```

## Privacy

Do not commit backups or raw device information. Redact local IP addresses, public keys, UMA client IDs, SSDP UDNs, MAC addresses, and Wi-Fi details from logs/issues.

## Project status

Early prototype. Read-only access to `/setup/eureka_info` was confirmed on one device running Cast firmware `3.72.446070`. Write behavior and cross-version compatibility are not yet confirmed. See [research notes](docs/research.md).
