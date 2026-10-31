# 04 — Turbulence from the gust's gap

Status: ⬜ ready once 02 is done

PRD D5. Real Weather writes `groundTurbulence = gust × 10.0194` with the gust's **peak** speed (`miz/mission.go`, `updateWind`; `MPSToEDUnits = 10.0194` in `weather/weather.go`), clamped by `gust-minimum` / `gust-maximum`.

- a. In the config and the preset (ticket 06): `gust-maximum = 50`, so Real Weather writes the peak unclamped and the gust can be read back: `gust = groundTurbulence / 10.0194` (m/s); the mean is the METAR wind of ticket 03 b.
- b. `turbulence_for_gust(mean, gust)` (module; its unit checked in ticket 02 c) gives the turbulence; `groundTurbulence` is written in DCS units, `m/s × 10.0194`, the factor Real Weather uses — to check against the measured table when it lands.
- c. If ticket 03 capped the wind, scale the gust gap by the same ratio before `turbulence_for_gust` caps it.
- d. No gust in the METAR: `groundTurbulence = 0`.

Done when: `08024G37KT` gives `groundTurbulence` 20.04 (2 m/s) while the cap holds; `27015KT` gives 0; a capped wind scales the gap first; when the in-game measurement's table lands in the module, only the module copy changes here.
