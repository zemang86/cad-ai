# Windows Setup Guide

## Prerequisites

- **Windows 10/11**
- **AutoCAD 2013 or later** installed and activated
- **Python 3.10+** — download from [python.org](https://www.python.org/downloads/)
  - During install, check **"Add Python to PATH"**
- **Git** — download from [git-scm.com](https://git-scm.com/download/win)

## Step 1: Clone and Install

Open **Command Prompt** or **PowerShell**:

```powershell
git clone https://github.com/zemang86/cad-ai.git
cd cad-ai
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[windows,dev]"
```

Verify:

```powershell
autocad-cmd version
```

## Step 2: Configure AutoCAD for COM Access

AutoCAD must allow COM automation:

1. Open AutoCAD
2. In the command line, type `SECURELOAD` and press Enter
3. Set value to `0`
4. Type `LEGACYCODESEARCH` and set to `1`
5. Restart AutoCAD

> AutoCAD must be **running** when you use the CLI or MCP server. The tool connects to the running AutoCAD instance via COM.

## Step 3: Test with a Real Drawing

Put some `.dwg` files in a test folder, then:

```powershell
# List what would change (dry run — use standardize with --report-only)
autocad-cmd standardize-layers --folder "C:\Users\YourName\drawings" --standard AIA --report-only

# Audit your drawings
autocad-cmd audit --folder "C:\Users\YourName\drawings" --standard UBBL

# Find and replace text (creates backups by default)
autocad-cmd change-text --folder "C:\Users\YourName\drawings" --find "TIMBER DOOR" --replace "ALUMINIUM DOOR"

# Rename a layer
autocad-cmd rename-layer --folder "C:\Users\YourName\drawings" --old-name "WALL" --new-name "A-WALL"
```

> Backups are saved to a `.backups` folder next to each DWG file. Use `--no-backup` to skip.

## Step 4: Using with Claude Code

Install Claude Code on Windows:

```powershell
npm install -g @anthropic-ai/claude-code
```

Then open the project in Claude Code:

```powershell
cd cad-ai
claude
```

Claude can now run CLI commands directly, e.g.:
- "Change all TIMBER DOOR to ALUMINIUM DOOR in my drawings folder"
- "Audit my submission drawings against UBBL standard"
- "Rename layer WALL to A-WALL across all plans"

## Step 5: MCP Server Setup (for Claude Desktop or other MCP clients)

### Windows (full AutoCAD + knowledge base)

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "autocad-batch-commander": {
      "command": "C:\\path\\to\\cad-ai\\.venv\\Scripts\\python.exe",
      "args": ["-m", "autocad_batch_commander.mcp_server.server"],
      "cwd": "C:\\path\\to\\cad-ai"
    }
  }
}
```

### macOS (knowledge base only — no AutoCAD needed)

Config location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "autocad-batch-commander": {
      "command": "/path/to/cad-ai/.venv/bin/python",
      "args": ["-m", "autocad_batch_commander.mcp_server.server"],
      "cwd": "/path/to/cad-ai"
    }
  }
}
```

> The `cwd` field is required so the server can locate the knowledge base and standards files.

After adding the config, **restart Claude Desktop**. The server starts automatically.

### Available MCP Tools

**Drawing operations** (Windows with AutoCAD running):
- `batch_change_text` — find/replace text across drawings
- `batch_rename_layer_tool` — rename layers
- `standardize_layers` — apply AIA/BS1192/UBBL standards
- `audit_drawings_tool` — check layer compliance

**Knowledge base & compliance** (any platform):
- `query_regulations` — ask natural language questions about Malaysian building regulations (UBBL, fire safety, planning, environmental, professional practice, etc.)
- `check_compliance_tool` — run structured compliance checks against rule sets (e.g. `ubbl-spatial`, `ubbl-fire-expanded`, `energy-efficiency`, `accessibility`, `environmental`, `bomba-fire-systems`)
- `list_available_rules` — show all available compliance rule sets

### Example prompts in Claude Desktop

Once configured, just chat naturally:
- "What is the minimum corridor width for commercial buildings?"
- "What are the fire certificate requirements from Bomba?"
- "Check fire compliance for a commercial high-rise"
- "What are the EIA thresholds for housing development?"
- "What are the architect fees under LAM?"
- "List all available compliance rule sets"

### Test the server manually

Before configuring Claude Desktop, verify the server starts:

```bash
# Windows
.venv\Scripts\python -m autocad_batch_commander.mcp_server.server

# macOS
.venv/bin/python -m autocad_batch_commander.mcp_server.server
```

If it starts without errors, you're good to add it to the config.

## Troubleshooting

### "AutoCAD.Application not found"
- Make sure AutoCAD is **running**
- Run your terminal as **Administrator**
- Check COM registration: open PowerShell and run:
  ```powershell
  python -c "import win32com.client; acad = win32com.client.Dispatch('AutoCAD.Application'); print('Connected:', acad.Name)"
  ```

### "Access Denied" errors
- Run terminal as Administrator
- Check that your user has write access to the drawing folder
- Disable antivirus temporarily if it blocks COM

### Drawings not saving
- Make sure drawings are not open in AutoCAD's editor (the tool opens them programmatically)
- Check that files are not read-only

### pywin32 import errors
- Ensure you installed with the windows extra: `pip install -e ".[windows]"`
- Try: `pip install pywin32 --force-reinstall`
