# VEAF-DCSServerBot

Fork VEAF de [DCSServerBot](https://github.com/Special-K-s-Flightsim-Bots/DCSServerBot) (remote `upstream`, mainteneur SpecialK).

## PR vers l'upstream

Toute PR destinée à `Special-K-s-Flightsim-Bots/DCSServerBot` se base sur `upstream/development`, jamais sur `master` (demande de SpecialK, 2026-10-12).

- `git fetch upstream`, puis créer la branche depuis `upstream/development`.
- Ouvrir la PR avec `--base development` sur le dépôt upstream.
- `CLAUDE.md` n'existe que dans notre fork et ne doit jamais arriver chez SpecialK. Avant d'ouvrir la PR, vérifier que `git diff --stat upstream/development...HEAD` ne liste pas `CLAUDE.md` (ni aucun autre fichier propre à VEAF).
