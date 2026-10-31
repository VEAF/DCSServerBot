# 01 — The station's real elevation

Status: ⬜ ready (no dependency)

Real Weather uses one `runway-elevation` (160 m in `realweather_v2.1.0/config.toml`) for every airfield: for the wind (replaced by ticket 03 anyway), the cloud base, the sea-level temperature and the QFF (PRD, Why 5).
`generate_config` (`extensions/realweather/extension.py`) already knows the ICAO (`get_icao_code`); it now also writes that station's elevation.

- a. **Lookup.** `get_station_elevation(icao) -> float | None`, in metres, from the METAR provider (PRD D2): `https://aviationweather.gov/api/data/metar?ids=<ICAO>&format=json`, field `elev` (station elevation in metres; EDFH 494, UGTB 468, OMAA 13 on 2026-10-31).
  The extension already uses `aiohttp`; time out after a few seconds.
  Cached per ICAO for the bot's lifetime: a station's elevation does not change.
- b. **Override.** An optional `elevations: {ICAO: metres}` in the extension's config (`nodes.yaml`, `RealWeather:`) wins over the lookup, to fix a wrong provider value or work offline.
- c. **Missing.** No override and no answer: a warning naming the mission and the ICAO; `runway-elevation` stays as configured, and ticket 03 uses sea level for the wind, with its own warning.
- d. **Write it.** `cfg['options']['weather']['runway-elevation'] = elevation` in `generate_config`, unless the preset sets it explicitly; the elevation is also kept on the instance for ticket 03.

Done when:

- unit tests: the lookup parsed from a recorded aviationweather answer; the override wins; a timeout gives `None` and the warning; `generate_config` writes the elevation into the merged config;
- on a test run with `ICAO_UGTB`, the generated `config.toml` (missions directory) holds the station's elevation (468 m or the provider's value), and the cloud base and temperature in the `.miz` move accordingly.
