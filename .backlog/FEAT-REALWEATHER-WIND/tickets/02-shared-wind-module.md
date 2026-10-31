# 02 — The shared wind module

Status: ⏸ waits for VMCT FEAT-MISSION-WIND-CHECK ticket 01 ([VEAF/VEAF-Mission-Creation-Tools#1228](https://github.com/VEAF/VEAF-Mission-Creation-Tools/pull/1228))

VMCT writes the DCS wind model once, as a standard-library module meant to be copied as is (`veaf_libs/dcs_wind.py`, Python ≥ 3.10, no I/O, no logging; contract in VMCT's `.backlog/FEAT-MISSION-WIND-CHECK/tickets/01-wind-model-brick.md`).
What this lot uses from it:

- `surface_wind`: the simulated wind at a point (round trip, tests);
- `ground_setting_for_surface_wind`: `atGround` for a wanted 10 m wind with `at2000` given; returns `1 − w` and `reliable` (`False` under 0.5); `ValueError` at 2,000 m MSL and above;
- `cap_setting_for_band(setting, ground_msl, max_knots, top_agl)`: caps the band, lowers `at2000` only when lowering `atGround` is not enough, and says so;
- `turbulence_for_gust(mean_kt, gust_kt)`: gust gap → turbulence, capped (2 m/s until the measured table).

- a. Copy `dcs_wind.py` and `dcs_wind_vectors.json` into `extensions/realweather/`, unchanged; the header names the VMCT commit it comes from and `MODEL_DCS_VERSION`.
- b. A test replays `dcs_wind_vectors.json` against the copy: a drift between the two repositories shows up as a failing test.
- c. Check the unit `turbulence_for_gust` returns (m/s, or `groundTurbulence` units at ×10.0194) and write it here; ticket 04 depends on it.

Done when the vectors pass under the bot's Python (3.11+), and the copy is byte-identical to the VMCT commit named in its header.
