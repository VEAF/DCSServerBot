# Foothold Plugin

This plugin provides integration with the Foothold mission framework for DCS World. It monitors mission save files, provides Discord commands to check campaign status, and serves a web-based SITAC (Situation Tactique) interface.

## Features

- **Automatic Detection**: Automatically detects Foothold missions via `foothold.status` file
- **Discord Commands**: `/foothold status`, `/foothold zones`, `/foothold mission` commands with rich embeds
- **Web Interface**: Standalone web server with interactive map showing zones, players, missions, and ejected pilots
- **Real-time Updates**: Periodic polling of mission save files with configurable refresh interval
- **In-memory Cache**: Fast access to mission data without constant file reads

## Configuration

Create or edit `config/plugins/foothold.yaml`:

```yaml
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

# Per-server configuration (optional)
DCS.release_server:
  enabled: false  # Disable for specific server
  update_interval: 60  # Override update interval
```

## Discord Commands

- `/foothold status [server]` - Show campaign progress and statistics
- `/foothold zones [server]` - List all zones with their status
- `/foothold mission [server]` - Show active missions information

## Web Interface

The plugin starts a standalone web server (default port 8081) that provides:

- Server list with last update times
- Interactive map with zones, connections, players, and ejected pilots
- Zone statistics and campaign progress
- Player rankings
- Active missions and ejected pilot lists

Access it at: `http://localhost:8081/foothold`

## Requirements

- DCS Foothold mission installed and running
- Mission must create `foothold.status` file in `Missions/Saves/`
- Python dependencies: `lupa`, `fastapi`, `uvicorn`, `jinja2`, `pydantic` (all included in DCSServerBot)

## Technical Details

- Uses `lupa` to parse Lua save files
- In-memory cache for fast access
- Automatic cleanup when `foothold.status` is removed
- Thread-based web server (non-blocking)
- Support for multiple DCS server instances

## Troubleshooting

**Plugin not detecting Foothold mission:**
- Check that `{instance.home}/Missions/Saves/foothold.status` exists
- Verify the file contains a valid mission file path
- Check plugin logs for errors

**Web interface not accessible:**
- Verify port is not blocked by firewall
- Check configuration in `foothold.yaml`
- Look for port conflicts with other services

**Data not updating:**
- Check `update_interval` in configuration
- Verify mission is running and creating save files
- Check file permissions on DCS Saved Games folder
