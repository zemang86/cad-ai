# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install (uses venv at .venv/)
.venv/bin/pip install -e ".[dev]"

# Run all tests
.venv/bin/pytest

# Run a single test file or test
.venv/bin/pytest tests/test_text_ops.py
.venv/bin/pytest tests/test_text_ops.py::test_case_insensitive_replace

# Lint
.venv/bin/ruff check .
.venv/bin/ruff format .

# CLI (entry point: autocad-cmd)
.venv/bin/autocad-cmd version
.venv/bin/autocad-cmd change-text --folder ./plans --find "OLD" --replace "NEW" --mock

# Knowledge base / compliance commands
.venv/bin/autocad-cmd query "minimum corridor width"
.venv/bin/autocad-cmd check-compliance-cmd --rules ubbl-spatial --building-type residential --mock
.venv/bin/autocad-cmd list-rules
```

## Architecture

Port/Adapter pattern — all business logic depends on `AutoCADPort` (Protocol), never on `win32com` directly.

```
CLI (Typer) / MCP Server (FastMCP)
        ↓
Operations (text_ops, layer_ops, audit_ops, compliance_ops)  ← pure Python, testable
Knowledge loader (knowledge/loader.py)                       ← reads Markdown knowledge base
        ↓
AutoCADPort (Protocol in acad/port.py)
        ↓
MockAutoCADAdapter (any platform)  or  RealAutoCADAdapter (Windows + pywin32)
```

**Dependency flow is one-way:** CLI/MCP → operations → acad port. Operations never import from `cli/` or `mcp_server/`.

The factory (`acad/factory.py`) auto-selects MockAdapter on non-Windows. All CLI commands accept `--mock` to force the mock adapter. When `--mock` is used from CLI, the factory pre-populates the adapter with sample architectural drawing data (text entities and layers) for every `.dwg` file found in the target folder, so commands produce realistic output.

## Key Patterns

- **Operations** all follow the same shape: take an `AutoCADPort` adapter + a Pydantic request model, iterate `.dwg` files via `utils/file_ops.get_dwg_files()`, open/modify/save/close each file, return an `OperationResult` or `AuditResult`.
- **Standards** are JSON files in `standards/` with `mappings` (old→new layer names) and `required_layers`. Used by `layer_ops.batch_standardize_layers()` and `audit_ops.audit_drawings()`.
- **Compliance rules** are JSON files in `standards/rules/` (e.g. `ubbl-spatial.json`, `ubbl-fire.json`). Each contains a `ComplianceRuleSet` with numeric thresholds, by-law references, and building-type filters. Used by `compliance_ops.check_compliance()`.
- **Knowledge base** is Markdown files in `knowledge/qa/` organized by source (ubbl/, fire-bylaws/). A topic index (`_index.md`) maps keywords to files. The loader (`knowledge/loader.py`) finds relevant files via keyword matching and returns content for Claude to synthesize. No vector DB — the corpus is small enough for direct context loading.
- **Config** uses pydantic-settings with env prefix `ACAD_CMD_` (e.g. `ACAD_CMD_LOG_LEVEL`). `standards_dir` points to `<repo>/standards/`, `knowledge_dir` points to `<repo>/knowledge/`.
- **Backups** go to `.backups/` subdirectory relative to each DWG file, with timestamped filenames.

## Testing Patterns

- `conftest.py` provides `mock_adapter` (pre-loaded with two drawings) and `dwg_folder` (tmp_path with dummy .dwg files).
- Operation tests define a local `_adapter_with_dwg_files(tmp_path)` helper that writes real dummy `.dwg` bytes to disk (so `get_dwg_files()` discovers them) AND registers those exact paths in MockAutoCADAdapter via `add_mock_drawing()`. Both steps are required.
- CLI tests use `typer.testing.CliRunner` with `--mock` and `--no-backup` flags. With `--mock`, the factory auto-populates sample data for files in the folder, so CLI tests get non-zero results.
- All tests run on macOS via the mock adapter — no AutoCAD needed.

## Models (models.py)

All Pydantic v2 models live in one file. Entities (`TextEntity`, `LayerEntity`) represent drawing objects. Request models (`TextReplaceRequest`, `LayerRenameRequest`, `ComplianceCheckRequest`, etc.) are operation inputs. Result models (`OperationResult`, `AuditResult`, `ComplianceCheckResult`, `RegulationResult`) are outputs. Compliance models (`ComplianceRule`, `ComplianceRuleSet`, `ComplianceFinding`) represent structured regulation rules.

## Windows Deployment

See `docs/windows-setup.md` for full guide. Key points:

- Install with `pip install -e ".[windows]"` to get pywin32
- AutoCAD must be **running** — the RealAutoCADAdapter connects via COM to the live instance
- Set `SECURELOAD=0` in AutoCAD to allow COM automation
- On Windows, the factory auto-selects `RealAutoCADAdapter` (no `--mock` needed)
- CLI commands work the same, just without `--mock` — they operate on real DWG files

## MCP Server

The MCP server (`mcp_server/server.py`) exposes seven MCP tools: the original four drawing operations plus `query_regulations`, `check_compliance_tool`, and `list_available_rules`. Launch with:

```bash
# Windows
.venv\Scripts\python -m autocad_batch_commander.mcp_server.server

# macOS (mock only)
.venv/bin/python -m autocad_batch_commander.mcp_server.server
```

For Claude Desktop integration, add to `claude_desktop_config.json` — see `docs/windows-setup.md`.

## Knowledge Base

Malaysian building regulations knowledge base in `knowledge/qa/`, covering UBBL, Fire By-Laws, and Bomba guidelines. Structure:

```
knowledge/
  qa/
    _index.md                   # Topic map — keyword → file mapping
    ubbl/                       # 6 files: general, operations, spatial, fire, parking, accessibility
    fire-bylaws/                # 2 files: fire certificate, fire escape
  raw/                          # Source PDFs (gitignored)
standards/
  rules/                        # Machine-readable compliance rules
    ubbl-spatial.json           # 17 dimensional rules (rooms, corridors, stairs, ventilation)
    ubbl-fire.json              # 13 fire safety rules (resistance, compartmentation, escape)
```

Each Markdown file has YAML frontmatter (`source_document`, `source_short`, `sections_covered`, `last_verified`) and content with bold thresholds and `> **Citation**` blocks.

Each JSON rule file contains a `ComplianceRuleSet` with rules that have: `id`, `by_law`, `check_type` (min_dimension/max_dimension/min_percentage/min_duration), `threshold`, `unit`, `building_type` filter, and `tags`.

To add new regulations: create Markdown files under the appropriate `knowledge/qa/` subdirectory, add entries to `_index.md`, and optionally add structured rules to `standards/rules/`.
