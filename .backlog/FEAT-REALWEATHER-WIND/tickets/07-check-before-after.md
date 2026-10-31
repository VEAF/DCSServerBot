# 07 — Check on a served mission, before and after

Status: ⬜ — the "before" part can be done now

- a. **Before** (any time, read only): take a `.miz` the servers produced for an `ICAO_` mission (the copy the bot writes next to the original), read `atGround`, `at2000`, `groundTurbulence` and the brief's METAR, and the METAR of that hour for the station.
  Expected: `atGround = 0.484 × METAR`, `at2000` = open-meteo 800 hPa (≤ 15 m/s), `groundTurbulence = 0`, brief wind = `atGround`.
- b. **After** (on a test instance first, then one server): the same reading. Expected: the 10 m wind computed from the `.miz` equals the METAR wind, or the capped one; band max ≤ 20 kt; `groundTurbulence` = the gust gap, capped; the brief consistent with it.
- c. **In game**, once: through the bridge, `atmosphere.getWind` 10 m above the station equals the METAR wind (VMCT's ticket 05 has the measuring tool).

Done when a and b are written in this ticket with their numbers, and c is done once.
