# 03 — The wind the METAR says, capped where helicopters fly

Status: ⬜ ready once 01 and 02 are done

PRD D1, D3, D4.

- a. **Make Real Weather write the METAR wind as is.** In `realweather_v2.1.0/config.toml` and the preset (ticket 06): `fixed-reference = true` (reference height 1 m, so `atGround = METAR × 1^0.143 = METAR`), `maximum = 50` (no cap by Real Weather), `scale-factor = 1.0`.
  With open-meteo up, `at2000` and `at8000` stay the 800 and 400 hPa winds.
  If open-meteo fails, Real Weather falls back to `updateWindLegacy`: `at2000 ≈ 2.97 × METAR`, `at8000 ≈ 3.6 ×`, directions veered at random by 0–45° per level. Acceptable, since the inversion takes `at2000` as given, but log it: Real Weather prints "continuing with legacy winds".
- b. **Read back.** After `run_realweather` has checked its output with `MizFile`, open it again (`MizFile.wind` has a getter and a setter in `core/mizfile.py`): METAR wind = `atGround` (speed; `dir` + 180 for "from"), `at2000` as written.
- c. **Invert.** `ground_setting_for_surface_wind(METAR wind, station elevation, at2000)` gives `atGround`.
  `reliable = False`: write it anyway, with a warning naming the airfield. `ValueError` (station at 2,000 m MSL or above): keep Real Weather's output, warn.
  No elevation (ticket 01 c): sea level, warn.
- d. **Cap.** `cap_setting_for_band(setting, elevation, 20 kt, 1,500 ft)`; when it lowered `at2000`, say so in the log.
  The cap (20 kt) and the band top (1,500 ft) are settings of the extension (ticket 06), not constants.
- e. **Write** `atGround` (and `at2000` if changed) with `MizFile.wind`, save, under the existing `_lock`.
  One log line per mission: ICAO, elevation, METAR wind, written `atGround`, simulated 10 m wind, band max, capped or not.
- f. Any failure in b to e: a warning, and Real Weather's output is kept (PRD, Constraints).

Done when:

- unit tests on the correction, with a `.miz` fixture and Real Weather's output simulated:
  - OMAA (13 m), `32011KT`, `at2000` 2.65 m/s from 047 → `atGround` 5.575 m/s towards 140, 11.0 kt from 320 at 10 m (VMCT's shared vector), then the cap brings the band to 20 kt;
  - a 25 kt METAR at sea level ends with a 20 kt band, about 9 kt at 10 m;
  - UGTB (468 m), `32012KT`, gives 12.0 kt at 10 m before the cap;
- a missing elevation and a module error both leave Real Weather's output, with a warning;
- the round trip `surface_wind(written setting)` gives the wanted wind, or the capped one, within 0.05 kt.
