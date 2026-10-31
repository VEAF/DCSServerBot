# FEAT-REALWEATHER-WIND — make the servers' real weather fly the wind the METAR says

Status: ⬜ ready — waits for ticket 01 of VMCT's FEAT-MISSION-WIND-CHECK (the shared wind module)

> **VEAF only. Never upstream.**
> `.backlog/` lives in the VEAF fork only and must never reach a pull request to SpecialK (`Special-K-s-Flightsim-Bots/DCSServerBot`).
> Upstream PR branches are cut from `upstream/development`, never from `veaf`; backlog changes are committed on their own, never in a commit that also touches code, so a cherry-pick of a fix never drags them along.
> Before opening any upstream PR: `git diff --stat upstream/development...HEAD` must list neither `.backlog/` nor any other VEAF-only file (`CLAUDE.md`, `dcssb-mcp/`, `extensions/realweather/dcs_wind.py` if the upstream PR is not about it).

## Why

On the servers (private1, private2, public1, public2, foothold2), every mission whose name carries `ICAO_XXXX` goes through DCS Real Weather (evogelsa) before it loads: MizEdit applies the preset `MatinTôt/Météo/Réelle/adaptée` (`VEAF-Servers/users/veaf/VEAF-DCSServerBot/config/nodes.yaml`, `presets.yaml`), whose `RealWeather:` block is run by `extensions/realweather/extension.py` (`generate_config`, `run_realweather`).

On 2026-10-31 a study decoded DCS's static-weather wind model from `Weather.dll` (DCS 2.9.31.29434) and checked it in game within 0.0003 m/s (whitepaper and `dcs_wind.py` on VMCT's branch `feature/dcs-wind-model`, [VEAF/VEAF-Mission-Creation-Tools#1227](https://github.com/VEAF/VEAF-Mission-Creation-Tools/pull/1227)).
Read against that model, Real Weather (same code in v2.1.0 and v2.5.0) gets the surface wind wrong:

1. **The ground setting is half the METAR.** `updateWind` writes `atGround = METAR × (1 / runway-elevation)^stability` (`miz/mission.go`, `windSpeed(1, …)`), with one `runway-elevation = 160` for every airfield (`realweather_v2.1.0/config.toml`): `atGround = 0.484 × METAR`.
   DCS then multiplies `atGround` by 1.0 (sea level) to 1.6 (500 m) at 10 m above the ground, so **the simulated 10 m wind is 0.48 to 0.78 × the METAR** on all our `ICAO_` airfields (4 to 494 m).
   Measured with the real weather of 2026-10-31 ~10Z: OMAA 11 kt announced → 5.4 kt simulated; ETAR 9 → 5.7; UGTB 12 → 9.2.
2. **The briefing shows the reduced wind.** Real Weather builds the METAR it inserts in the brief from what it wrote (`GenerateMETAR`, `Data[1]`): `32005KT` at OMAA for a real `32011KT`. The extension also keeps that string as `self.metar` (shown on Discord).
3. **Gusts become turbulence the wrong way.** `groundTurbulence = gust × 10.0194`, where `gust` is the gust's **peak** speed, not its gap over the mean wind: `08024G37KT` gives 19 m/s of turbulence for a 6.7 m/s gap. On 2026-10-29 the cap of 7 m/s made helicopters nearly unflyable (Marteau du Golan); turbulence has been off since (`gust-maximum = 0`).
4. **The 15 m/s cap is applied to all three levels.** `maximum = 15` (config and preset) also clips `at2000` and `at8000`: a 46 kt jet at 400 hPa becomes 29 kt. Meanwhile it does not protect the low layer, since it caps the setting, not the simulated wind.
5. **The single runway elevation skews clouds, temperature and QFF too.** Cloud base = METAR base + 160 m MSL, sea-level temperature = station + 160 × 6.5 °C/km, QNH → QFF with 160 m (`mission.go`): at UGTB (468 m) clouds sit 308 m too low and the temperature is 2 °C too cold.

What Real Weather gets right and we keep: `at2000` and `at8000` are real winds aloft (open-meteo, 800 and 400 hPa).

Discovery note with sources, line numbers and the computed cases: side-session note `meteo-serveurs-decouverte.md` (2026-10-31); this PRD carries everything needed from it.

## What

Real Weather keeps fetching the weather and writing the mission; the extension then corrects what it wrote, with the same wind module as VMCT.

| # | What | Status | Ticket |
|---|---|---|---|
| 01 | The station's real elevation: fetched by ICAO before Real Weather runs, written as `runway-elevation` (fixes clouds, temperature, QFF) and kept for the wind | ⬜ | [01](tickets/01-station-elevation.md) |
| 02 | The shared wind module copied from VMCT, its shared test vectors replayed here | ⬜ | [02](tickets/02-shared-wind-module.md) |
| 03 | The wind: Real Weather writes the METAR wind as is, the extension inverts it into `atGround` with the real `at2000`, and caps the simulated wind at 20 kt over 0–1,500 ft above the ground | ⬜ | [03](tickets/03-wanted-wind.md) |
| 04 | Turbulence from the gust's gap over the mean, capped (2 m/s until the in-game measurement) | ⬜ | [04](tickets/04-turbulence.md) |
| 05 | The METAR in the brief and on Discord says the wind DCS simulates | ⬜ | [05](tickets/05-briefing-metar.md) |
| 06 | Settings, schema, deployment in VEAF-Servers, documentation | ⬜ | [06](tickets/06-config-deploy-docs.md) |
| 07 | Check on a served mission, before and after | ⬜ | [07](tickets/07-check-before-after.md) |

02 waits for VMCT's ticket 01 (the module is not written yet). 01 can be done first, alone. 03 needs 01 and 02; 04 needs 02; 05 needs 03 and 04.

## Decisions

Taken by David on 2026-10-31; details under them are recommendations by default.

- **D1 — correct after Real Weather, in the extension; no fork of Real Weather.**
  The binary from evogelsa stays as released; `extensions/realweather/extension.py` post-processes the `.miz` it produced, which it already opens with `MizFile` to check it.
  A PR to evogelsa (invert the DCS model, use the station's elevation) comes **later**, once this runs on our servers; it would let us drop the post-processing.
- **D2 — the elevation is the METAR station's**, from the METAR provider, looked up by ICAO (ticket 01).
- **D3 — the wanted wind is the METAR wind at 10 m above the station**, inverted with the model at that elevation, with **the real `at2000` as given** (open-meteo), not a multiple of `atGround`.
  Raising `at2000` to ≥ 2.14 × `atGround` was rejected: it changes nothing below 1,000 ft and invents wind between 1,000 and 2,000 m (OMAA: 23 kt at 2,000 m where open-meteo gives 5).
- **D4 — cap: the simulated wind never exceeds 20 kt anywhere from the ground to 1,500 ft above it** ("above 20 kt it gets hard for a helicopter"); strong wind aloft is fine.
  The cap lowers `atGround` first, and `at2000` only when the terrain is high enough for the 2,000 m level to dominate the band (the module's `cap_setting_for_band` does both and says when it touched `at2000`).
  Price, from the model: the band's top is 2.1 × the 10 m wind at sea level, 1.6 × at 231 m, 1.35 × at 468 m, so the surface wind is at most about 9 kt on a coastal airfield, 12 kt at 231 m, 15 kt at 468 m.
  Real Weather's own `maximum` no longer caps anything (set to 50): `at2000` and `at8000` stay real.
- **D5 — turbulence is back, as the gap gust − mean wind, capped** — 2 m/s until the in-game measurement (session « Mesure en jeu de la turbulence DCS », VMCT) gives a table from gust gap to `groundTurbulence`; the module's `turbulence_for_gust` will follow that table.
  The 2026-10-29 decision (turbulence off) is reversed.
- **D6 — clouds, temperature and QFF are fixed in the same lot**, by the real `runway-elevation` of D2.

## Constraints

- Python ≥ 3.11 (`install.py`); the server runs 3.13.12.
- The extension must keep working when the correction cannot be made (no elevation, module error): it logs a warning naming the mission and the ICAO, and leaves Real Weather's output as is, rather than failing the mission load.
- Servers sharing a missions directory share `config.toml`: everything stays under the existing `_lock`.
