# 📝 Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-03-06
### Added
- Integrated `StatusPrinter` for a much cleaner and visually informative CLI output with ANSI colors and task progress indicators.
- Implementation of a global `REPO_URL` constant for consistent repository referencing.

### Changed
- Refactored project structure to use a dedicated `config/` directory for configuration files (`connections.csv`, `elements.csv`, `locations.csv`, `config.json`).
- Updated the script to automatically search for configuration files in the `config/` directory by default.
- Enhanced "Smart Search" logic for connection files in the CLI, scanning both the root and `config/` folders.
- Improved the final execution summary to include aggregated statistics for processed nodes and connections.

## [B1.33] - 2026-03-06
### Added
- New CLI argument `-w / --out` to specify a custom output directory for diagrams and logs.
- Support for underscore-based headers in CSV files (`endpoint_a`, `endpoint_b`, `connection_text`), maintaining backward compatibility with hyphenated headers.
- New `TO_REVIEW` layer in Geographic layout for elements lacking coordinates.
- Automatic central spiral positioning for unlocated elements in the geographic map to prevent overlap.
- Specific `geographic_review.log` generation listing elements needing coordinate verification.
- `scipy` dependency for optimized organic layout calculation on large graphs.

### Fixed
- `KeyError` crashes in `read_connections` due to header naming variations (`-` vs `_`).
- `KeyError` in Geographic layout when connection endpoints lacked positions.
- `UnboundLocalError` in generator error handling logic.
- Missing connection text labels when using underscore headers in CSV.

### Changed
- Consolidated all output files (logs and diagrams) into the directory specified by `-w`.
- Renamed the script to `network-topology-generator.py` and updated all internal references.
- Standardized remaining Portuguese variables and terms to English.
- Improved logging and error reporting for large dataset processing.

---

## [B1.32] - Previous Base Version
- Optimized topology generation with CLI and GUI support.
- 4 layout algorithms (Circular, Organic, Geographic, Hierarchical).
- Advanced customization via `config.json`.
- Automatic regionalization and legends.
