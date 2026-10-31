# 05 — The METAR says the simulated wind

Status: ⬜ ready once 03 and 04 are done

Real Weather inserts its own METAR in the brief, after the line `==Real Weather METAR==` (`realweather.mission.brief.insert-key`), built from what it wrote; the extension keeps it as `self.metar` (parsed from Real Weather's output) for Discord.
After tickets 03 and 04, with `fixed-reference` and `gust-maximum = 50`, that METAR shows the station's wind and gust: right as long as nothing was capped.

- a. When ticket 03 or 04 changed the wind or the gust, rewrite the wind group of that METAR, in the brief and in `self.metar`, to what DCS simulates 10 m above the station (`surface_wind`), gust included, and append `RMK VEAF WIND CAPPED FROM <original group>`.
  Recommendation by default: the brief describes what the pilot will fly, and the remark keeps the real report visible.
- b. The brief text lives in the mission's dictionary (key `descriptionText`, `l10n/DEFAULT/dictionary`); `MizFile` has no accessor for it today: add one, or edit the dictionary the way Real Weather does.

Done when a capped case shows the simulated group and the remark in the `.miz` brief and in `self.metar`, and an uncapped case leaves Real Weather's METAR untouched.
