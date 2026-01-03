# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Foothold plugin with comprehensive unit tests
- Configuration system for Foothold plugin with environment variable expansion
- Support for zones, players, missions, connections, and ejected pilots
- Campaign progress calculation
- Web interface configuration

### Fixed
- Unit test fixtures for Foothold plugin
- Import system for plugin modules
- PYTHONPATH configuration for test execution
- Zone neutral state handling in campaign progress calculations
- Player data loading from Lua save files

### Changed
- Updated test framework to use proper plugin module structure
- Migrated from `yaml` to `ruamel.yaml` for configuration parsing