# AutoCAD Batch Commander

Batch operations for AutoCAD drawings + Malaysian building regulations knowledge base and compliance checking.

Built for architects, draftsmen, and architecture firms who need to make bulk revisions across multiple DWG files and verify compliance with UBBL, Fire By-Laws, and other Malaysian building regulations.

## Installation

```bash
git clone https://github.com/zemang86/cad-ai.git
cd cad-ai
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

On Windows with AutoCAD:

```bash
.venv\Scripts\pip install -e ".[dev,windows]"
```

## Quick Start

### Query Building Regulations

```bash
# Ask about any Malaysian building regulation
autocad-cmd query "minimum corridor width"
autocad-cmd query "fire appliance access"
autocad-cmd query "hospital fire safety"
autocad-cmd query "SPAH rainwater harvesting"
autocad-cmd query "demolition requirements"

# Check compliance against structured rule sets
autocad-cmd check-compliance-cmd --rules ubbl-spatial --building-type residential --mock
autocad-cmd check-compliance-cmd --rules ubbl-fire-expanded --building-type commercial --mock

# List all available rule sets
autocad-cmd list-rules
```

### Batch Drawing Operations

Use `--mock` on macOS/Linux (no AutoCAD needed). On Windows with AutoCAD running, omit `--mock`.

```bash
# Batch find and replace text
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

## MCP Server (Claude Desktop Integration)

The MCP server exposes all features as tools for AI agents. Launch it:

```bash
# macOS (mock mode)
.venv/bin/python -m autocad_batch_commander.mcp_server.server

# Windows (real AutoCAD)
.venv\Scripts\python -m autocad_batch_commander.mcp_server.server
```

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "autocad-batch-commander": {
      "command": "/path/to/cad-ai/.venv/bin/python",
      "args": ["-m", "autocad_batch_commander.mcp_server.server"]
    }
  }
}
```

This gives Claude access to 7 tools: text replace, layer rename, layer standardize, audit, query regulations, check compliance, and list rules.

## Knowledge Base

Comprehensive Malaysian building regulations knowledge base covering:

| Category | Files | Topics |
|----------|-------|--------|
| **UBBL** | 11 | General provisions, spatial requirements, fire safety, parking, accessibility, structural, constructional, demolition, 2021 amendment |
| **Fire By-Laws** | 5 | Fire certificate, fire escape, fire-fighting systems, fire door ratings, high-rise fire |
| **Legislation** | 4 | Act 133 (SDBA), Act 172 (planning), strata management, housing development |
| **Agencies** | 3 | JKR, CIDB, DOE |
| **Standards** | 4 | MS 1525 energy, MS 2680 residential energy, MS 1184 accessibility, MS fire standards |
| **Green Building** | 2 | GBI certification, solar/renewable |
| **Local Authority** | 3 | OSC process, DBKL, Selangor PBTs |
| **Professional** | 3 | LAM architects, BEM engineers, BQSM quantity surveyors |
| **Infrastructure** | 3 | TNB electrical, water/sewerage, telecom |
| **Building Types** | 4 | High-rise, industrial, healthcare, educational |

### Compliance Rule Sets

7 machine-readable JSON rule sets with numeric thresholds for automated checking:

| Rule Set | Rules | Coverage |
|----------|-------|----------|
| `ubbl-spatial` | 17 | Room sizes, ceiling heights, corridors, staircases, ventilation |
| `ubbl-fire` | 13 | Fire resistance, compartmentation, escape routes |
| `ubbl-fire-expanded` | 20 | Compartment areas by purpose group, travel distances, fire access |
| `bomba-fire-systems` | 12 | Hose reel, hydrant, dry riser, fire doors |
| `energy-efficiency` | 8 | OTTV, RTTV, roof U-values, BEI |
| `environmental` | 10 | EIA thresholds, effluent, noise |
| `accessibility` | 12 | Ramps, handrails, toilets, lifts |

## Architecture

Port/Adapter pattern — all business logic is pure Python and testable without AutoCAD:

```
CLI (Typer) / MCP Server (FastMCP)
        |
Operations (text, layer, audit, compliance)    <-- pure Python
Knowledge loader (keyword search)              <-- reads Markdown KB
        |
AutoCADPort (Protocol)
        |
  +-----+------+
  |            |
MockAdapter  RealAdapter
(any OS)     (Windows + AutoCAD)
```

## Windows Setup

See `docs/windows-setup.md` for full guide. Key points:

- AutoCAD must be **running** — connects via COM automation
- Set `SECURELOAD=0` in AutoCAD to allow COM
- Commands work the same, just without `--mock`

## Testing

```bash
.venv/bin/pytest
```

All 46 tests run against the mock adapter — no AutoCAD installation required.

## License

MIT
