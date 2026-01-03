# Foothold Plugin Tests

## Test Structure

- `units/` - Unit tests for core Foothold logic
- `integration/` - Integration tests (require DCSServerBot environment)
- `fixtures/` - Test data (Lua save files)

## Running Unit Tests

Unit tests can be run independently:

```powershell
# From plugin directory
cd d:\dev\_VEAF\VEAF-DCSServerBot\plugins\foothold
pytest tests/units/ -v
```

## Running Integration Tests

Integration tests require a running DCSServerBot instance with mocked servers.

**Note**: Integration tests need to be refactored to work with the plugin architecture.
They currently test the standalone FastAPI app and need adaptation for the plugin's web server.

## Test Fixtures

Test fixtures contain Lua save files simulating various Foothold scenarios:

- `test_hidden/` - Zones with hidden=true
- `test_progress/` - Different campaign progress states
- `test_missions/` - Active missions
- `test_ejected/` - Ejected pilots

## Known Issues

1. Integration tests (`test_api.py`) need refactoring for plugin architecture
2. Tests assume specific file paths relative to plugin directory
3. Mock DCS Server objects needed for full integration testing

## TODO

- [ ] Refactor integration tests for plugin architecture
- [ ] Add tests for Discord commands
- [ ] Add tests for web server lifecycle
- [ ] Add tests for sitac caching
- [ ] Mock DCS Server and Instance objects
