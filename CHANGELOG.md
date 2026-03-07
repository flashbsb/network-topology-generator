# 📝 Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-06
### Fixed
- **Draw.io compatibility**: Refactored the diagram XML generation to use standard `mxCell` tags for layers and nodes instead of `object` tags, which resolves visibility issues on complex geographic layouts.
- **XML Stability**: Added proper XML escaping for all labels and names using the `html` module, preventing broken diagrams due to special characters like `&`.

## [1.1.9] - 2026-03-06
### Fixed
- **Geographic Review Log**: Improved the logic for identifying elements without coordinates during geographic layout generation, ensuring they are correctly added to the `geographic_review_*.log` file even if their layer wasn't changed to `TO_REVIEW`.

## [1.1.8] - 2026-03-06
### Changed
- **Terminal UI Refinement**: Removed the redundant title line from the final summary for a cleaner transition between file results and the execution report.

## [1.1.7] - 2026-03-06
### Fixed
- **Terminal Summary Restoration**: Restored the execution statistics (total time, files processed, and infrastructure count) to the final terminal report.

## [1.1.6] - 2026-03-06
### Changed
- **Terminal UI Polish**: Added a blank line between the initial file information and the progress bar for better visual separation.

## [1.1.5] - 2026-03-06
### Changed
- **Terminal UI Refactor**: Reorganized the command-line output to show file-specific success summaries only after the progress bar completes.
- **Enhanced Summary**: Expanded the final execution summary with additional repository links for related tools (`network-data-extractor`, `backbone-network-topology-generator`).

## [1.1.4] - 2026-03-06
### Fixed
- **Empty Page Rendering**: Resolved an issue where "REFLECTOR +INNER" and "PEERING TRANSIT + INNER" pages appeared empty. This was caused by connections crossing between pages referencing pruned layers; filtering has been synchronized to ensure valid XML generation.

## [1.1.3] - 2026-03-06
### Added
- **Automatic Dependency Validator**: Integrated a robust pre-import check for required packages (`networkx`, `chardet`, `numpy`, `scipy`, `tkinter`).
- **Interactive Installation Guide**: If dependencies are missing, the script now provides platform-specific installation commands for Windows, Debian/Ubuntu, Fedora, and Arch Linux, including instructions for `pip` and system packages.

## [1.1.2] - 2026-03-06
### Added
- **Empty Layer Pruning**: Layers without any elements (nodes or connections) are now automatically omitted from the generated Draw.io diagrams and Legend to reduce clutter.
- **Empty Page Skipping**: Pages defined in configuration that result in no rendered elements are now completely skipped.

## [1.1.1] - 2026-03-06

## [1.0.3] - 2026-03-06
### Fixed
- Suppressed `RuntimeWarning` from `networkx` regarding duplicate backends (`nx-loopback`) to ensure a cleaner CLI output.

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
- [x] Refactor terminal output presentation
    - [x] Update `StatusPrinter.show_summary` with expanded repository info
    - [x] Reorder file success messages to appear after progress bar
- [x] Fix geographic review logging for nodes without coordinates
- [x] Refactor Draw.io XML for better stability and visibility
lements needing coordinate verification.
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
