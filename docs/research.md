# Research notes

## Confirmed on one device

- `GET http://<ip>:8008/setup/eureka_info` returned HTTP 200.
- `GET https://<ip>:8443/setup/eureka_info` returned HTTP 200; the device presents a certificate Windows does not trust by default.
- Tested firmware reports Cast build `3.72.446070`.
- The `opt_in` object reported `stats: true`, `crash: true`, and `opencast: false`.
- `OPTIONS /setup/set_eureka_info` returned HTTP 200 with no `Allow` header. That does not establish which request methods or fields are supported.
- Several guessed `/setup/*` paths returned 404; `/setup/reboot` returned 405 to the attempted GET. The project does not attempt reboot.

## Protocol references to verify

- Chromecast tools repository: https://github.com/garethcheyne/chromecast-tools
- Chromecast MCP API documentation: https://docs.rs/chromecast-mcp/latest/chromecast_mcp/cast/index.html
- Public Cast API example: https://gist.github.com/1mm0rt41PC/78e134d43e5badf3cc999bdf33e1fdd5

These references suggest that `set_eureka_info` is used by third-party tooling for configuration fields, including opt-in preferences. They do not prove identical behavior on every firmware. The write path is experimental and requires direct verification.

## Next research tasks

1. Validate whether the stats/crash preference write is accepted and persists on Cast 3.72.446070.
2. Capture Chromecast network traffic during idle, backdrop, and active casting sessions.
3. Identify destinations based on observed evidence before drafting a DNS blocklist.
4. Test candidate blocks one at a time and document effects on discovery, casting, playback, updates, and setup.
5. Add rollback guidance before implementing router-specific automation.

## Privacy rules for contributors

Never commit raw `/setup/eureka_info` output, device IPs, public keys, UMA client IDs, SSDP UDNs, MAC addresses, Wi-Fi SSIDs, or private backups.