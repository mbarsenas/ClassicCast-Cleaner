# Research notes

## Confirmed on one device

- Device is a classic Chromecast running Cast build `3.72.446070`.
- `GET http://<ip>:8008/setup/eureka_info` returned HTTP 200.
- `GET https://<ip>:8443/setup/eureka_info` returned HTTP 200; the device presents a certificate Windows does not trust by default.
- The `opt_in` object reported `stats: true`, `crash: true`, and `opencast: false`.
- `OPTIONS /setup/set_eureka_info` returned HTTP 200 with no `Allow` header. This does not establish supported methods or fields.
- The project GET-only probe returned HTTP 200 for `/setup/eureka_info`.
- The probe returned HTTP 404 for `/setup/configured_networks`, `/setup/supported_locales`, `/setup/supported_timezones`, `/setup/supported_languages`, and `/setup/supported_time_formats` on this firmware.
- `GET /setup/set_eureka_info` returned HTTP 405. This indicates GET is not accepted at that path; it does not prove a POST payload will work.
- `/setup/reboot` returned HTTP 405 to the attempted GET in an earlier test. The project does not attempt reboot.
- `POST /setup/set_eureka_info` with `{"opt_in":{"stats":false,"crash":false}}` returned HTTP 401 on 2026-10-29. No settings change was confirmed; a pre-change backup was saved locally.
- Protocol documentation reports that protected setup endpoints require the `cast-local-authorization-token` header, while `/setup/eureka_info` is an exception. The CLI now supports the token through `CAST_LOCAL_AUTHORIZATION_TOKEN`; token acquisition is deliberately not automated.

These results are from one device and firmware version only. A 404 for a guessed path is not evidence that the capability is absent; the path may be incorrect or unavailable on this build.

## Protocol references to verify

- Chromecast tools repository: https://github.com/garethcheyne/chromecast-tools
- Chromecast MCP API documentation: https://docs.rs/chromecast-mcp/latest/chromecast_mcp/cast/index.html
- Public Cast API example: https://gist.github.com/1mm0rt41PC/78e134d43e5badf3cc999bdf33e1fdd5

These references suggest that `set_eureka_info` is used by third-party tooling for configuration fields, including opt-in preferences. They do not prove identical behavior on every firmware. The write path is experimental and requires direct verification.

## Next research tasks

1. Validate whether the stats/crash preference write is accepted and persists on Cast 3.72.446070, with a pre-change backup and read-back verification.
2. Capture Chromecast network traffic during idle, backdrop, and active casting sessions.
3. Identify destinations based on observed evidence before drafting a DNS blocklist.
4. Test candidate blocks one at a time and document effects on discovery, casting, playback, updates, and setup.
5. Add rollback guidance before implementing router-specific automation.

## Privacy rules for contributors

Never commit raw `/setup/eureka_info` output, device IPs, public keys, UMA client IDs, SSDP UDNs, MAC addresses, Wi-Fi SSIDs, or private backups.
