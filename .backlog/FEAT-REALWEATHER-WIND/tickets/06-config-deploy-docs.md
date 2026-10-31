# 06 — Settings, schema, deployment, documentation

Status: ⬜ ready with 03

- a. **Extension settings** (`nodes.yaml`, under `RealWeather:`), all optional: `wind-correction: {enabled: true, band-max-kt: 20, band-top-ft: 1500}`, `turbulence-max-mps: 2`, `elevations: {}` (ticket 01 b).
  They are read from `self.config`; `generate_config` only merges keys that already exist in Real Weather's `config.toml`, so they never leak into it: check it stays so.
- b. **Schema**: add them to `extensions/realweather/schemas/realweather_schema.yaml`; the bot validates `nodes.yaml` against it.
- c. **VEAF-Servers** (other repository, same lot):
  - `users/veaf/realweather_v2.1.0/config.toml`: `fixed-reference = true`, `maximum = 50`, `gust-maximum = 50`, `scale-factor = 1.0`, comments updated;
  - `users/veaf/VEAF-DCSServerBot/config/presets.yaml`, preset `Météo/Réelle/adaptée`: `wind.maximum: 50`, `gust-maximum: 50`, a comment pointing to the extension's cap;
  - `nodes.yaml`: the settings of a;
  - deployed with `Sync-Server.ps1`, then a bot restart; DCS itself needs no restart.
- d. **Docs**:
  - `VEAF-Servers/docs/ORGANISATION.md`, section « L'heure et la météo des missions »: the « pas de turbulence » and « borné à 15 m/s » bullets describe the new behaviour;
  - `VEAF-Servers/tools/README.md`: the Real Weather row and the turbulence paragraph;
  - `extensions/realweather/README.md` in the fork: a VEAF section.
