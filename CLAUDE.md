# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install (uses venv at .venv/)
.venv/bin/pip install -e ".[dev]"

# Install with web server support
.venv/bin/pip install -e ".[web]"

# Install with AI chat support (OpenAI + Supabase)
.venv/bin/pip install -e ".[web,ai]"

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

# Web server (requires [web] extras)
.venv/bin/autocad-cmd serve
.venv/bin/autocad-cmd serve --port 3000
```

## Architecture

Port/Adapter pattern — all business logic depends on `AutoCADPort` (Protocol), never on `win32com` directly.

```
CLI (Typer) / MCP Server (FastMCP) / Web API (FastAPI)
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
- **Knowledge base** is Markdown files in `knowledge/qa/` organized by source (ubbl/, fire-bylaws/). A topic index (`_index.md`) maps keywords to files. The loader (`knowledge/loader.py`) finds relevant files via keyword matching and returns content for Claude to synthesize. For AI Chat, the knowledge base is also embedded into Supabase pgvector (463 chunks) for semantic retrieval. Each file includes a `## Cross-References` section linking related By-Laws, Schedules, Acts, and Standards across the knowledge base.
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

Malaysian building regulations knowledge base in `knowledge/qa/`, covering UBBL, Fire By-Laws, legislation, agencies, standards, green building, local authorities, professional practice, infrastructure, and building types. Structure:

```
knowledge/
  qa/
    _index.md                   # Topic map — keyword → file mapping (~160 keyword entries)
    ubbl/                       # 18 files covering all UBBL Parts and key Schedules
      01-general-provisions.md      # Part I — definitions, interpretation
      02-building-operations.md     # Part II — plan submission (By-laws 3–29)
      03-spatial-requirements.md    # Part III — room sizes, corridors, ventilation
      04-fire-requirements.md       # Part VII — fire resistance, compartmentation, escape
      05-parking-requirements.md    # Parking ratios, bay dimensions
      06-accessibility-requirements.md  # OKU access, ramps, handrails
      07-temporary-works.md         # Part IV — hoarding, scaffolding
      08-structural-requirements.md # Part V — loads, foundations
      09-constructional-requirements.md # Part VI — staircases, swimming pools, party walls, lifts
      10-2021-amendment.md          # 2021 Amendment summary (energy, OTTV, lightning)
      11-demolition.md              # Part IA — demolition
      12-fire-alarm-systems.md      # Part VIII — smoke control, atriums, risers, emergency power
      13-miscellaneous.md           # Part IX — exemptions, standards, building failure
      14-schedule-fifth.md          # Schedule 5 — purpose groups, compartment dimensions
      15-schedule-seventh.md        # Schedule 7 — travel distances, occupant load, exit capacity
      16-schedule-ninth.md          # Schedule 9 — fire resistance periods
      17-schedule-tenth.md          # Schedule 10 — fire alarm/extinguishment requirements
      18-schedule-eleventh.md       # Schedule 11 — staircase landing dimensions
    fire-bylaws/                # 5 files: fire certificate, fire escape, fire fighting systems, fire door ratings, highrise fire
    legislation/                # 4 files: Act 133 SDBA, Act 172 planning, strata management, housing development
    agencies/                   # 3 files: JKR, CIDB, DOE
    standards/                  # 4 files: MS 1525 energy, MS 2680 residential energy, MS 1184 accessibility, MS fire standards
    green-building/             # 2 files: GBI certification, solar/renewable
    local-authority/            # 3 files: OSC process, DBKL, Selangor PBTs
    professional/               # 3 files: LAM architects, BEM engineers, BQSM quantity surveyors
    infrastructure/             # 3 files: TNB electrical, water/sewerage, telecom
    building-types/             # 4 files: high-rise, industrial, healthcare, educational
  raw/                          # Source PDFs (gitignored)
standards/
  rules/                        # Machine-readable compliance rules (8 rule sets)
    ubbl-spatial.json           # 17 dimensional rules (rooms, corridors, stairs, ventilation)
    ubbl-fire.json              # 13 fire safety rules (resistance, compartmentation, escape)
    ubbl-fire-expanded.json     # 25 expanded fire rules (Part VIII, atriums, smoke control, risers, emergency power)
    ubbl-constructional.json    # 16 constructional rules (staircases, swimming pools, party walls, lifts)
    bomba-fire-systems.json     # 12 fire fighting system rules (hose reel, hydrant, dry riser, fire doors)
    energy-efficiency.json      # 8 energy rules (OTTV, RTTV, roof U-values, BEI)
    environmental.json          # 10 environmental rules (EIA thresholds, effluent, noise)
    accessibility.json          # 12 accessibility rules (ramps, handrails, toilets, lifts)
scripts/
  extract_ubbl.py               # PDF extraction tool — reads UBBL PDF, splits by Part/Schedule/By-law
  embed_knowledge.py            # Embed knowledge base Markdown into Supabase pgvector
  setup_supabase.sql            # DDL migration for chat tables, RPC, and view
```

Each Markdown file has YAML frontmatter (`source_document`, `source_short`, `sections_covered`, `last_verified`) and content with bold thresholds and `> **Citation**` blocks.

Each JSON rule file contains a `ComplianceRuleSet` with rules that have: `id`, `by_law`, `check_type` (min_dimension/max_dimension/min_percentage/min_duration), `threshold`, `unit`, `building_type` filter, and `tags`.

To add new regulations: create Markdown files under the appropriate `knowledge/qa/` subdirectory, add entries to `_index.md`, and optionally add structured rules to `standards/rules/`.

### PDF Extraction Script

`scripts/extract_ubbl.py` extracts raw text from the UBBL PDF, split by Part and By-law, for creating curated knowledge base files:

```bash
# Install pymupdf
.venv/bin/pip install pymupdf

# Extract to temp directory
.venv/bin/python scripts/extract_ubbl.py "sample/UKBS 1984 1C.pdf" --output-dir /tmp/ubbl-extract
```

The script outputs raw text files — final knowledge base files should be manually curated with proper formatting.

## Web API & UI

FastAPI app in `web/api.py` exposes the knowledge base and compliance features over HTTP. Single-page web UI in `web/templates/index.html` (vanilla HTML/CSS/JS, no build step). CAD-inspired dark/light theme with blueprint grid background, sidebar navigation, and bottom status bar. Theme preference persists via localStorage. No LLM API — search returns raw markdown from knowledge base files.

### Tabs

- **Setup Guide** — installation, CLI usage, MCP server configuration, Windows/AutoCAD setup, API docs, knowledge base coverage
- **AI Chat** — conversational AI powered by OpenAI GPT-5 Mini with RAG retrieval from Supabase pgvector. Feature-flagged, hidden when `ACAD_CMD_CHAT_ENABLED=false`
- **UBBL 2021** — interactive browser for UBBL content with TOC, filtering, and search
- **Regulation Search** — keyword search across the knowledge base, renders Markdown results
- **Compliance Check** — select rule sets and building type, returns matching rules with thresholds
- **Rule Browser** — browse individual rule sets and their rules

### Endpoints

```
GET  /                           — Web UI (single-page app)
GET  /api/health                 — Health check (includes chat_enabled flag)
POST /api/query                  — Query knowledge base (body: {"question": "..."})
GET  /api/rules                  — List all rule sets
GET  /api/rules/{rule_set}       — Get rules in a specific rule set
POST /api/compliance/check       — Check compliance (body: ComplianceCheckRequest)
POST /api/chat/session           — Create chat session with consent
POST /api/chat                   — Send chat message → SSE streamed response
POST /api/feedback               — Submit thumbs up/down feedback
```

Drawing operations (change-text, rename-layer, etc.) are CLI-only — they require Windows + AutoCAD and are not exposed via the web API.

### Deployment

```bash
# Local
autocad-cmd serve

# Vercel (production)
# Auto-deploys from main branch. Entrypoint: api/index.py
# Set env vars in Vercel dashboard: ACAD_CMD_CHAT_ENABLED, ACAD_CMD_OPENAI_API_KEY,
# ACAD_CMD_SUPABASE_URL, ACAD_CMD_SUPABASE_KEY

# Docker
docker build -t cad-ai . && docker run -p 8000:8000 cad-ai

# Docker Compose
docker compose up
```

### Vercel Deployment

The app deploys to Vercel as a serverless FastAPI function. Key files:

- `api/index.py` — Vercel entrypoint, sets `sys.path` and env defaults for knowledge/standards dirs
- `vercel.json` — Region config (sin1 Singapore)
- `.python-version` — Pins Python 3.12 for Vercel runtime
- `requirements.txt` — Fallback deps list (Vercel primarily uses `pyproject.toml`)

Web+AI deps (fastapi, openai, supabase, etc.) are in base `dependencies` in `pyproject.toml` so Vercel auto-installs them. `config.py` uses `_find_project_root()` to resolve knowledge/standards paths in both dev (src layout) and Vercel (installed package) environments.

**Local dev is unaffected** — the Vercel files are only used during Vercel builds.

## AI Chat (RAG Pipeline)

Conversational AI chat powered by OpenAI with Supabase pgvector for semantic retrieval. Feature-flagged via `ACAD_CMD_CHAT_ENABLED` (default: `false`).

### Architecture

```
Frontend (SSE streaming) → FastAPI endpoints → RAG pipeline
                                                  ↓
                                    OpenAI embeddings → Supabase pgvector search
                                    Few-shot examples ← feedback (thumbs up/down)
                                    OpenAI GPT-5 Mini streaming completion
                                                  ↓
                                    Persist messages + context to Supabase
```

### Module: `chat/`

| File | Purpose |
|------|---------|
| `chat/models.py` | Pydantic models: ChatMessage, ChatRequest, SessionConsentRequest, FeedbackRequest, ChunkMatch |
| `chat/prompts.py` | System prompt template, few-shot formatting, context chunk formatting |
| `chat/client.py` | Supabase client singleton (lazy-init from settings) |
| `chat/embeddings.py` | OpenAI embed_text/embed_texts, pgvector search_similar, fetch_highly_rated_examples |
| `chat/rag.py` | RAG pipeline: embed query → search → build messages → stream OpenAI → persist |

### Chat API Endpoints

```
POST /api/chat/session   — Create session with consent
POST /api/chat           — Send message → SSE streamed response
POST /api/feedback       — Submit thumbs up/down on assistant message
```

All chat endpoints return 503 when `ACAD_CMD_CHAT_ENABLED=false`. Health endpoint includes `chat_enabled: bool`.

### Config (env vars)

```
ACAD_CMD_OPENAI_API_KEY          — OpenAI API key
ACAD_CMD_OPENAI_MODEL            — Model name (default: gpt-5-mini)
ACAD_CMD_OPENAI_EMBEDDING_MODEL  — Embedding model (default: text-embedding-3-small)
ACAD_CMD_SUPABASE_URL            — Supabase project URL
ACAD_CMD_SUPABASE_KEY            — Supabase publishable key (sb_publishable_*) or legacy anon key
ACAD_CMD_CHAT_ENABLED            — Feature flag (default: false)
ACAD_CMD_CHAT_MAX_HISTORY        — Max conversation turns sent to LLM (default: 10)
ACAD_CMD_CHAT_MAX_CONTEXT_CHUNKS — Max RAG chunks retrieved (default: 6)
ACAD_CMD_CHAT_SIMILARITY_THRESHOLD — Minimum cosine similarity (default: 0.4)
```

### Setup

1. Run `scripts/setup_supabase.sql` against your Supabase project (SQL Editor)
2. Embed the knowledge base: `.venv/bin/python scripts/embed_knowledge.py`
3. Start with chat enabled:
   ```bash
   ACAD_CMD_CHAT_ENABLED=true \
   ACAD_CMD_OPENAI_API_KEY=sk-... \
   ACAD_CMD_SUPABASE_URL=https://xxx.supabase.co \
   ACAD_CMD_SUPABASE_KEY=sb_publishable_... \
   .venv/bin/autocad-cmd serve
   ```

### Embedding Pipeline (`scripts/embed_knowledge.py`)

Chunks Markdown files by H2/H3 headings, embeds via OpenAI, upserts to Supabase pgvector.

```bash
.venv/bin/python scripts/embed_knowledge.py              # incremental
.venv/bin/python scripts/embed_knowledge.py --force       # re-embed all
.venv/bin/python scripts/embed_knowledge.py --file ubbl/03-spatial-requirements.md
.venv/bin/python scripts/embed_knowledge.py --dry-run     # preview chunks
```

### Dependencies

Install with: `.venv/bin/pip install -e ".[web,ai]"`

The `ai` extras group includes: `openai`, `supabase`, `tiktoken`, `sse-starlette`.
