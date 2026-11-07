# AGENTS.md

## Repository Scope

These instructions apply to the entire repository. If a deeper directory later gets its own `AGENTS.md` or `AGENTS.override.md`, that file should narrow or override these rules for work in that subtree.

## Project Overview

- `traffic-monitor` is a Go service that polls Mihomo `/connections`, aggregates traffic into SQLite, and serves an embedded web UI. This local fork also provides a Python gateway for viewing two independent collectors.
- The Go backend embeds `web/`; the Python gateway serves the same assets from disk. Changes to `web/` require rebuilding the Go binary but are read from disk by the gateway.
- There is no frontend build step in this repository. The UI is plain static assets under `web/` embedded by Go.

## Important Files

- `main.go`: application entrypoint, HTTP routes, SQLite logic, Mihomo integration, and embedded asset serving.
- `main_test.go`: primary automated test coverage for backend logic and HTML/script assertions.
- `web/index.html`: embedded UI structure.
- `web/styles.css`: embedded UI styling.
- `web/app.js`: embedded UI behavior and API calls.
- `gateway.py`: loopback-only dashboard and source switcher; proxies local API requests and read-only Lenovo traffic requests. `test_gateway.py` covers its request policy and offline handling.
- `README.md`: user-facing behavior and operational expectations. Update when behavior materially changes.

## Working Agreements

- Keep changes surgical. Do not refactor unrelated areas while fixing one issue.
- Preserve the independent Go collectors, embedded static frontend, SQLite persistence, and the optional local Python gateway; do not start a second collector against an existing database.
- Prefer extending existing patterns in `main.go` and the current frontend files over introducing new layers or frameworks.
- Do not add Node-based tooling, frontend bundlers, or new production dependencies unless explicitly requested.
- Avoid changing persisted behavior, API payloads, or database defaults unless the task requires it. When you do, update tests.

## UI and Frontend Rules

- Treat `web/index.html`, `web/styles.css`, and `web/app.js` as a tightly coupled unit.
- Favor small HTML changes and CSS-first fixes before adding new JavaScript complexity.
- Keep the UI dense and operational rather than marketing-styled. This project is a monitoring console.
- Preserve mobile behavior when adjusting desktop layouts.

## Backend Rules

- Keep Mihomo-facing behavior explicit and observable. Prefer clear logging around auto-switch or restore behavior over opaque control flow.
- Keep SQLite schema and query changes backward-compatible when possible.
- Reuse existing helpers and response patterns instead of adding parallel abstractions.

## Validation

- Run `go test ./...` after code changes.
- Run `python -m unittest test_gateway` for gateway changes and `node --check web/app.js` for JavaScript changes. Go SQLite builds require CGO and a C compiler.
- If you change HTTP handlers, persistence rules, or auto-switch behavior, add or update tests in `main_test.go`.
- If you change UI copy or layout, sanity-check the affected HTML/CSS/JS together and avoid leaving mismatched labels or dead selectors.

## Commit Scope

- Do not commit unrelated untracked files such as local notes, temporary docs, or `.claude/` contents unless the user explicitly asks for them.
- Keep commits grouped by user-visible outcome, not by file type.

## Release Versioning

- Keep the release tag and the page footer version in sync.
- When bumping a release, update the footer version string in `web/index.html`.
- Use the same version string for the git tag, prefixed with `v`.

## Useful Commands

```bash
go test ./...
go build -o traffic-monitor .
```

## Local Deployment Snapshot (2026-11-07)

- This checkout is `D:\chat\traffic-monitor-lan`; the existing Windows collector executable and database are in `D:\chat\clash-traffic-monitor`. Do not replace, stop, or delete them without checking ownership and preserving the database.
- Windows collector listens on `127.0.0.1:18080`; `python gateway.py` serves the two-source dashboard on `127.0.0.1:18081`. Current-user Run entries start the collector and gateway at login. Actual operation depends on the configured Python executable and paths remaining available.
- Lenovo (`lenovo_r720`, user `laoq`) runs `traffic-monitor-lan.service` as a systemd user service in `~/.local/share/traffic-monitor-lan`, with its own SQLite database and Mihomo controller on loopback port 9090. The server listens on port 18080; `TRAFFIC_MONITOR_LAN_HOST` enables only GET traffic endpoints and health for the configured LAN Host. Verify current service state before changes.
- `gateway.py` currently targets Lenovo's LAN IP `192.168.0.105`; if it changes, update the gateway and the server's allowed Host together. Keep remote settings/control endpoints inaccessible over LAN; do not expose controller secrets, credentials files, databases, or browsing history in commits or logs.
- The gateway's Lenovo view is read-only; local settings and automatic-switch controls are disabled while it is selected. Collectors run independently, filter DIRECT traffic in the current deployment, poll every 5 seconds and batch flush at 10-minute intervals; short connections can be missed. Per-app attribution depends on Mihomo metadata; clients on other devices may appear without their application names.
- Startup entries and systemd service were verified enabled and running on 2026-11-07; a full machine-reboot test has not been performed. `README.md` and release notes largely describe upstream behavior rather than the two-source local deployment.
