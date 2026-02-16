# AutoCAD Batch Commander

Batch operations for AutoCAD drawings — text find/replace, layer rename, standardization, and audit.

Built for architects, draftsmen, and architecture firms who need to make bulk revisions across multiple DWG files.

## Installation

```bash
pip install -e ".[dev]"
```

On Windows with AutoCAD:

```bash
pip install -e ".[dev,windows]"
```

## Quick Start

```bash
# Show version
autocad-cmd version

# Batch find and replace text (use --mock for testing without AutoCAD)
autocad-cmd change-text \
  --folder ./plans \
  --find "TIMBER DOOR" \
  --replace "ALUMINIUM DOOR" \
  --mock

# Rename a layer across all drawings
autocad-cmd rename-layer \
  --folder ./plans \
  --old-name "WALL" \
  --new-name "A-WALL" \
  --mock

# Standardize layers to AIA/BS1192/UBBL
autocad-cmd standardize-layers \
  --folder ./plans \
  --standard AIA \
  --mock

# Audit drawings for layer compliance
autocad-cmd audit \
  --folder ./plans \
  --standard AIA \
  --mock
```

## Architecture

Uses a Port/Adapter pattern so all business logic is pure Python and testable without AutoCAD:

```
Operations (pure Python) --> AutoCADPort (Protocol)
                                  |
                          +-------+-------+
                          |               |
                   MockAdapter      RealAdapter
                   (macOS/test)     (Windows+AutoCAD)
```

## Standards

Includes layer mapping files for:

- **AIA** — American Institute of Architects
- **BS1192** — British Standard
- **UBBL** — Uniform Building By-Laws (Malaysia)

Custom standards can be provided as JSON files.

## Testing

```bash
pytest
```

All tests run against the mock adapter, so no AutoCAD installation is required.

## License

MIT
