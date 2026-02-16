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
```

## Architecture

Port/Adapter pattern — all business logic depends on `AutoCADPort` (Protocol), never on `win32com` directly.

```
CLI (Typer) / MCP Server (FastMCP)
        ↓
Operations (text_ops, layer_ops, audit_ops)  ← pure Python, testable
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
- **Config** uses pydantic-settings with env prefix `ACAD_CMD_` (e.g. `ACAD_CMD_LOG_LEVEL`). The `standards_dir` setting points to `<repo>/standards/` by default.
- **Backups** go to `.backups/` subdirectory relative to each DWG file, with timestamped filenames.

## Testing Patterns

- `conftest.py` provides `mock_adapter` (pre-loaded with two drawings) and `dwg_folder` (tmp_path with dummy .dwg files).
- Operation tests define a local `_adapter_with_dwg_files(tmp_path)` helper that writes real dummy `.dwg` bytes to disk (so `get_dwg_files()` discovers them) AND registers those exact paths in MockAutoCADAdapter via `add_mock_drawing()`. Both steps are required.
- CLI tests use `typer.testing.CliRunner` with `--mock` and `--no-backup` flags. With `--mock`, the factory auto-populates sample data for files in the folder, so CLI tests get non-zero results.
- All tests run on macOS via the mock adapter — no AutoCAD needed.

## Models (models.py)

All Pydantic v2 models live in one file. Entities (`TextEntity`, `LayerEntity`) represent drawing objects. Request models (`TextReplaceRequest`, `LayerRenameRequest`, etc.) are operation inputs. Result models (`OperationResult`, `AuditResult`) are outputs.

## Windows Deployment

See `docs/windows-setup.md` for full guide. Key points:

- Install with `pip install -e ".[windows]"` to get pywin32
- AutoCAD must be **running** — the RealAutoCADAdapter connects via COM to the live instance
- Set `SECURELOAD=0` in AutoCAD to allow COM automation
- On Windows, the factory auto-selects `RealAutoCADAdapter` (no `--mock` needed)
- CLI commands work the same, just without `--mock` — they operate on real DWG files

## MCP Server

The MCP server (`mcp_server/server.py`) exposes the same four operations as MCP tools. Launch with:

```bash
# Windows
.venv\Scripts\python -m autocad_batch_commander.mcp_server.server

# macOS (mock only)
.venv/bin/python -m autocad_batch_commander.mcp_server.server
```

For Claude Desktop integration, add to `claude_desktop_config.json` — see `docs/windows-setup.md`.
