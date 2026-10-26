# Plugin RestAPI
This API provides a very simple RestAPI that you can use together with the [WebService](../../services/webservice/README.md).
You can use it to power the [DCS Statistics Dasboard](https://github.com/Penfold-88/DCS-Statistics-Dashboard).

## Configuration
As RestAPI is an optional plugin, you need to activate it in main.yaml first like so:
```yaml
# config/main.yaml
opt_plugins:
  - restapi
```

You can configure the RestAPI endpoints in your config\plugins\restapi.yaml like so:
```yaml
# config/plugins/restapi.yaml
DEFAULT:
  prefix: /stats            # Optional: use this prefix
  api_key: aaabbbcccc       # Optional: API key to be used to secure the API
  endpoints:                 # endpoint configuration
    servers:                # /servers
      filter:               # config parameter (in this case, the server filter list)
        - 'MyPrivateServer' # Do not show a server named "MyPrivateServer"
        - '(.*)Private(.*)' # Do not show any server that has "Private" in its name 
      include_weather: true # Include weather information in /servers endpoint (default: true)
    server_attendance:      # /server_attendance 
      enabled: true         # Enable the server attendance statistics endpoint (default: true)
```

> [!WARNING]
> Do NOT use a prefix if you work with the DCS Statistics Dasboard!

## RestAPI
The following commands are available through the API. For detailed parameter definitions, response models, and schemas, see [API Documentation](API.md).

| API | GET / POST | Parameters | Description |
|-----|------------|------------|-------------|
| /airbase | GET | server_name: string, airbase_name: string | Get information for a given airbase on a given server. |
| /airbase/atis | GET | server_name: string, airbase_name: string | Get ATIS information for an airbase on a given server. |
| /airbase/capture | POST | server_name: string, airbase_name: string, coalition: int | Capture the airbase. |
| /airbase/warehouse | GET | server_name: string, airbase_name: string | Get warehouse information for an airbase on a given server. |
| /airbase/warehouse/item | POST | server_name: string, airbase_name: string, item: string, value: int | Set warehouse item quantity for an airbase on a given server. |
| /airbases | GET | server_name: string | Get a listing of all airbases on a given server. |
| /convertCoordinates | GET | server_name: string, coordinates: string | Convert provided coordinate string into other formats. |
| /credits | POST | nick: string, [date: string | None], [campaign: string | None] | Get campaign credits for players |
| /current_server | GET | nick: string, [date: string | None] | Server name a player is flying on |
| /events | GET | ucid: string, start_time: datetime, end_time: datetime, [event: string | None], [init_type: string | None], [offset: int | None], [limit: int | None] | Get mission events for players |
| /getuser | POST | [nick: string], [discord_id: string] | Get users by name |
| /greenieboard | POST | [date: string | None], [server_name: string | None] | Get a greenieboard |
| /highscore | GET | [server_name: string], [period: string], [limit: int] | Get highscore statistics for players |
| /instance/mission/load | POST | server_name: string, mission_name: string | Load a mission on a given server. |
| /instance/mission/pause | POST | server_name: string | Pause the mission on a given server. |
| /instance/mission/restart | POST | server_name: string, [run_extensions: bool], [use_orig: bool], [when_empty: bool] | Restart the mission on a given server. Defaults: run_extensions=false, use_orig=true, when_empty=false. With when_empty=true and players connected, the restart waits until the server is empty (needs the Scheduler plugin) and the response status is "pending"; 409 if an action is already pending. |
| /instance/mission/unpause | POST | server_name: string | Unpause the mission on a given server. |
| /instance/missions | GET | server_name: string | Return all missions for a given server. |
| /instance/restart | POST | server_name: string | Restart a server. |
| /instance/shutdown | POST | server_name: string, [force: bool], [maintenance: bool], [when_empty: bool] | Shut a server down (terminates the DCS process), like /server shutdown. Defaults: force=false, maintenance=true, when_empty=false. force kills the process at once, but never cuts a session with when_empty. With when_empty=true and players connected, the shutdown waits until the server is empty (needs the Scheduler plugin) and the response status is "pending"; 409 if an action is already pending. |
| /instance/start | POST | server_name: string | Start a server. |
| /instance/stop | POST | server_name: string | Stop a server. |
| /leaderboard | GET | what: string, [order: string], [query: string | None], [limit: int | None], [offset: int | None], [server_name: string | None] | Get leaderbord information |
| /linkme | POST | discord_id: string, [force: bool] | Link your Discord account to your DCS account |
| /mission/bullseyes | GET | server_name: string | Get the bullseye coordinates for blue and red coalitions in the current mission. |
| /mission/drawings | GET | server_name: string | Get mission drawing objects grouped by drawing layer. |
| /mission/group/waypoints | GET | server_name: string, group_name: string, group_type: string | Get the lat/lon waypoints for a named group in the current mission. |
| /mission/unit | GET | server_name: string, unit_name: string | Get mission unit data including current position, loadout, navaids, and waypoints. |
| /mission/upload | POST | server_name: string, file: string, filename: string, load_after: bool | Upload a .miz mission file to the server. |
| /modulestats | POST | nick: string, [date: string | None], [server_name: string | None] | Get module statistics |
| /node/restart | POST | [node_name: string] | Restart a node, or all nodes (default), like /node restart. The bot reloads its configuration. The response is sent before the node serving the API restarts. |
| /player_info | POST | nick: string, [date: string | None], [server_name: string | None] | Get player information |
| /player_squadrons | POST | nick: string, [date: string | None] | List of player squadrons |
| /server_attendance | GET | [server_name: string] | Get detailed server attendance statistics |
| /servers | GET | [server_name: string | None] | List all servers, the active mission (if any) and the active extensions |
| /serverstats | GET | [server_name: string] | List the statistics of a whole group |
| /squadron_credits | POST | name: string, [campaign: string] | Squadron campaign credits |
| /squadron_members | POST | name: string | List squadron members |
| /squadrons | GET | [limit: int], [offset: int] | List all squadrons and their roles |
| /stats | POST | nick: string, [date: string | None], [server_name: string | None], [last_session: bool | None] | Get player statistics |
| /topkdr | GET | [limit: int], [offset: int], [server_name: string] | Get top KDR statistics for players |
| /topkills | GET | [limit: int], [offset: int], [server_name: string] | Get top kills statistics for players |
| /traps | POST | nick: string, [date: string | None], [limit: int | None], [offset: int | None], [server_name: string | None] | Get traps for players |
| /traps/img | GET | trap_id: int | Get trap image for a player |
| /trueskill | GET | [limit: int], [offset: int], [server_name: string] | Get TrueSkill:tm: statistics for players |
| /weaponpk | POST | nick: string, [date: string | None], [server_name: string | None] | Get PK statistics for all weapons of a specific players |

> [!NOTE]
> To get more detailled API documentation with test options, please enable debug in your WebService config and 
> access https://localhost:9876/docs.

## Log endpoints
`/node/logs` and `/node/log` read the bot log (`logs/dcssb-<node>.log` and its rotated files), `/instance/logs` and `/instance/log` read the DCS log of a server (`dcs.log`, `dcs.log.old` and the `dcs-YYYYMMDD-HHMMSS.log` copies the bot makes at shutdown).
They are meant for diagnostic tools: why does this server not start, what did the bot do at 03:00, did the ED login fail.

| API            | GET / POST | Parameters                                                                                   |
|----------------|------------|----------------------------------------------------------------------------------------------|
| /node/logs     | GET        | [node_name: string]                                                                          |
| /node/log      | GET        | [node_name: string], [file], [contains], [level], [since], [until], [lines], [tail], [cursor] |
| /instance/logs | GET        | server_name: string                                                                          |
| /instance/log  | GET        | server_name: string, [file], [contains], [level], [since], [until], [lines], [tail], [cursor] |

* **They exist only when an `api_key` is set**: logs contain player names, UCIDs and IP addresses.
* A file is chosen by node or server, then optionally by a name taken from the listing. A path is never accepted.
* Filters: `contains` (case-insensitive text, repeat it to require several terms), `level` (minimum: `debug`, `info`, `warning`, `error`, `critical`), `since` and `until` (ISO 8601, UTC if no offset, or a duration such as `30m`, `2h`, `1d`), `lines` (200 by default, 2000 at most), `tail` (the last matching entries, or the first ones with `false`).
* The lines that follow an entry without a timestamp of their own (a Python traceback, a multi-line Lua error) stay with that entry, so a level filter never cuts a traceback.
* Each answer carries a `cursor`. Pass it back to get only what was written since. It survives a log rotation: the end of the old file is read first, then the new one (`rotated: true`, and `new_file_at` says where the new file starts in `lines`); if the old file is gone, `gap: true` says lines may be missing.
* Every read is bounded (16 MiB read, 1 MiB returned, lines cut at 8 KiB); `more: true` says a limit was reached.
* **This version reads the files of the node that serves the RestAPI only**: a server or a bot log on another node answers 501. DCSServerBot 3.0.5 reads every node.

```bash
# the last warnings and errors of a server, with a cursor
curl -s -H "X-API-Key: $KEY" "https://bot.example.org/instance/log?server_name=my_instance&level=warning&lines=50"
# later: only what was written since
curl -s -H "X-API-Key: $KEY" "https://bot.example.org/instance/log?server_name=my_instance&cursor=<cursor of the previous answer>"
# the ED logins of the last two hours
curl -s -H "X-API-Key: $KEY" "https://bot.example.org/instance/log?server_name=my_instance&contains=ASYNCNET&since=2h"
```

> [!IMPORTANT]
> Never publish the API without HTTPS: put a reverse proxy (Caddy, nginx, IIS) in front of it, and keep the WebService listening on `127.0.0.1`.

## New Features

### Weather Information
The `/servers` endpoint now includes real-time weather data for running DCS servers:
```json
{
  "weather": {
    "temperature": 16.0,
    "wind_speed": 0.968,
    "wind_direction": 290,
    "pressure": 765.0,
    "visibility": 5000,
    "clouds_base": 0,
    "clouds_density": 0,
    "precipitation": 0,
    "fog_enabled": false,
    "dust_enabled": false
  }
}
```

### Server Attendance Statistics
The `/server_attendance` endpoint provides comprehensive server attendance analytics:

- **Server attendance statistics**: Current active players, unique players, total playtime hours, and Discord member engagement for different time periods (24h, 7d, 30d)
- **Top statistics**: Most popular theatres, missions, and modules by playtime and usage
- **Daily trends**: Daily unique player counts for the last 7 days to analyze server activity patterns
- **Combat statistics**: Total sorties, kills, deaths, and PvP statistics from mv_serverstats

**Global statistics (no parameters):**
```bash
GET /server_attendance
```

**Server-specific statistics (using DCS server name):**
```bash
GET /server_attendance?server_name=VEAF (www.veaf.org) [fr] - Private Foothold 2
```

**Server-specific statistics (using instance alias):**
```bash
GET /server_attendance?server_name=foothold2_server
```

**Response example:**
```json
{
  "current_players": 8,
  "unique_players_24h": 15,
  "total_playtime_hours_24h": 45.5,
  "discord_members_24h": 12,
  "unique_players_7d": 35,
  "total_playtime_hours_7d": 180.2,
  "discord_members_7d": 28,
  "unique_players_30d": 85,
  "total_playtime_hours_30d": 720.8,
  "discord_members_30d": 65,
  "daily_trend": [
    {"date": "2025-12-24", "unique_players": 15},
    {"date": "2025-12-25", "unique_players": 18}
  ]
}
```

### Server Name Resolution
All endpoints that accept a `server_name` parameter now support both server naming conventions seamlessly:
- **Instance alias**: `foothold2_server` (from nodes.yaml configuration)
- **DCS server name**: `VEAF (www.veaf.org) [fr] - Private Foothold 2` (from servers.yaml configuration)

The resolution is handled transparently by the `get_resolved_server()` method, which:
1. Checks if the provided name is already a full DCS server name
2. If not, searches instance aliases and returns the corresponding DCS server name
3. Returns both the resolved name and server object for use in endpoints

This approach ensures consistent behavior across all endpoints while maintaining simple, readable SQL construction patterns.
