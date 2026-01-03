# Plan: Transformer foothold-sitac en plugin DCSServerBot

Intégration de foothold-sitac comme plugin DCSServerBot avec interface web autonome sur port configurable, cache mémoire, et commandes Discord avec embeds riches.

## Steps

1. **Créer la structure du plugin** dans `VEAF-DCSServerBot/plugins/foothold/` : `__init__.py`, `version.py`, `commands.py`, `listener.py`, `schemas/foothold_schema.yaml`, `README.md`, copier `static/` et `templates/`

2. **Migrer la logique métier** : Adapter `foothold.py` pour utiliser `server.instance.home`, remplacer `list_servers()` par itération sur les serveurs DCSServerBot, conserver `lupa`, adapter `config.py` pour la nouvelle structure

3. **Créer la configuration** : `config/plugins/foothold.yaml` avec `enabled: true`, `update_interval: 120`, `web.port: 8081`, `web.host: 0.0.0.0`, et section `map` complète (url_tiles, alternative_tiles, min_zoom, max_zoom)

4. **Implémenter le serveur web** : Dans `cog_load()`, démarrer Uvicorn sur thread séparé, enregistrer les routes adaptées de `foothold_router.py` et `foothold_api_router.py`, dans `cog_unload()` arrêter proprement le serveur

5. **Implémenter le cache mémoire** : Ajouter `self.sitacs: dict[str, Sitac] = {}` dans la classe plugin, méthodes `get_sitac(server_name)`, `update_sitac(server, sitac)`, `remove_sitac(server_name)` pour gérer le cache

6. **Ajouter le polling périodique** : `@tasks.loop(seconds=config.update_interval)` scanne tous les serveurs, détecte `{instance.home}/Missions/Saves/foothold.status`, charge/met à jour le cache, retire du cache si `foothold.status` disparaît

7. **Créer les commandes Discord** : `/foothold status`, `/foothold zones`, `/foothold mission` avec `ServerTransformer`, créer embeds Discord riches avec couleurs par coalition, barre de progression, statistiques formatées

8. **Adapter les tests** : Copier `tests/` dans `plugins/foothold/tests/`, adapter avec mocks pour `Server`, `Instance`, tester le cache et les embeds Discord

## Further Considerations

1. **Permissions Discord** : Restreindre les commandes `/foothold` à certains rôles (`@utils.app_has_role('DCS')`) ou laisser accessible à tous ?

2. **Logs** : Niveau de logging pour le polling (DEBUG pour chaque scan, INFO seulement sur changements détectés) ?

3. **Performance** : Si beaucoup de serveurs, exécuter le scan de manière asynchrone avec `asyncio.gather()` ou séquentielle suffit ?

## Décisions prises

- **Dépendances** : Utiliser `lupa` (déjà disponible dans DCSServerBot), pas besoin d'ajouter de nouvelles dépendances
- **Configuration** : Auto-détection des serveurs Foothold via `foothold.status` + possibilité d'activer/désactiver par serveur
- **Interface web** : Port séparé configurable (défaut: 8081), pas d'intégration dans le WebService de DCSServerBot
- **Stockage** : Cache mémoire pour commencer (pas de DB pour l'instant)
- **Erreurs** : Retirer du cache si `foothold.status` disparaît
- **Discord** : Embeds riches avec couleurs et formatage
- **Shutdown** : Arrêt propre du serveur Uvicorn dans `cog_unload()`

## Configuration exemple

```yaml
# config/plugins/foothold.yaml
DEFAULT:
  enabled: true
  update_interval: 120  # Scan interval in seconds
  
  web:
    host: "0.0.0.0"
    port: 8081
  
  map:
    url_tiles: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    alternative_tiles:
      - name: "OpenStreetMap"
        url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      - name: "Terrain"
        url: "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg"
    min_zoom: 8
    max_zoom: 11

DCS.release_server:
  enabled: false  # Disable for specific server
```

## Structure du plugin

```
plugins/foothold/
├── __init__.py
├── version.py
├── commands.py          # Discord commands + web server
├── listener.py          # Event listener (minimal/optional)
├── foothold.py          # Core logic (migrated)
├── config.py            # Config models
├── dependencies.py      # FastAPI dependencies
├── schemas.py           # Pydantic schemas
├── README.md
├── schemas/
│   └── foothold_schema.yaml
├── static/              # CSS, JS, images
│   ├── css/
│   └── js/
├── templates/           # Jinja2 templates
│   ├── base.html
│   └── foothold/
└── tests/               # Unit and integration tests
    ├── fixtures/
    ├── units/
    └── integration/
```
