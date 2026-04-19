# perimeter-scout — Librarian Manifest

_Generated: `2026-04-19T20:13:16Z` by `librarian/build_manifest.py`._

> **Source of truth for the Mapping & Inventory Librarian.** This file is regenerated on every push; do not hand-edit. To change the structure, edit `librarian/build_manifest.py`.

## Purpose

Perimeter Scout is the **Aegis Security Core** for the Pioneer Ecosystem. It exposes a FastAPI backend (with an optional Streamlit dashboard) that performs real-time posture intelligence, IP monitoring with auto-ban, and a battery of detectors (requests, auth, config, integrity, network, behavior). It also acts as a client of the Pioneer Trader **Mapping & Inventory** hub for fleet inventory, T.I.A. risk summaries, and RAG ingest/query proxying.

## Module map

| Path | Role |
|---|---|
| `backend/main.py` | FastAPI bootstrap, CORS, middleware, router registration. |
| `backend/core/` | Module registry, event bus, policy engine, module interface. |
| `backend/middleware/aegis_middleware.py` | IP-allow + `AEGIS_COMMANDER_TOKEN` gate. |
| `backend/security/ip_monitor.py` | Auto-ban after repeated auth failures. |
| `backend/routers/` | `security`, `modules`, `admin`, `inventory` HTTP routes. |
| `backend/services/perimeter_scout/` | Aegis core + detectors + interceptors. |
| `backend/services/admiral/` | Admiral trading engine stub. |
| `backend/services/admirai/` | Admirai orchestrator. |
| `backend/services/mapping_inventory/client.py` | HTTP client for the M&I hub. |
| `backend/services/agents/` | Agent base + TIA agent + future template. |
| `streamlit_app/app.py` | Streamlit dashboard. |
| `tasks/security_digest.py` | Daily security digest background task. |
| `utils/drive_auth.py` | Google Drive auth (stub). |
| `config/policy.aegis.json` | Aegis policy document loaded by the policy engine. |
| `librarian/` | This integration directory. |

## External integrations

- **Pioneer Trader Mapping & Inventory hub** (`PIONEER_TRADER_URL`): fleet inventory, cockpit health, TIA summary, RAG `/v1/ingest` and `/v1/query` proxy.
- **Citadel Nexus Faceplate (Vercel HUD)** (`https://citadel-nexus-private.vercel.app`): allowed CORS origin; consumes `/health/*` and `/api/v1/system/status`.
- **Hugging Face Space** (`huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME`): deployment target, mirrored by `.github/workflows/hf_sync.yml`.
- **Google Drive** (`utils/drive_auth.py`): stub today; intended Citadel folder sync via the CITADEL-BOT tunnel.

## Environment variables

| Variable | Referenced in |
|---|---|
| `AEGIS_COMMANDER_TOKEN` | `backend/middleware/aegis_middleware.py` |
| `ALLOWED_ORIGINS` | `backend/main.py` |
| `API_BASE_URL` | `streamlit_app/app.py` |
| `GITHUB_SHA` | `backend/routers/system_ops.py` |
| `GIT_COMMIT` | `backend/routers/system_ops.py` |
| `HF_COMMIT_SHA` | `backend/routers/system_ops.py` |
| `PIONEER_TRADER_URL` | `backend/services/mapping_inventory/client.py` |

## HTTP endpoints

> Note: routers are mounted with `prefix='/api/v1'` in `backend/main.py`, so `/security/...` becomes `/api/v1/security/...` in production.

| Method | Path (in source) | Source file |
|---|---|---|
| GET | `/api/v1/system/status` | `backend/routers/system_ops.py` |
| GET | `/events` | `backend/routers/modules_ops.py` |
| GET | `/fleet` | `backend/routers/inventory_ops.py` |
| GET | `/health` | `backend/routers/inventory_ops.py` |
| GET | `/health` | `backend/routers/modules_ops.py` |
| GET | `/health/live` | `backend/main.py` |
| GET | `/health/ready` | `backend/main.py` |
| GET | `/health/security` | `backend/main.py` |
| POST | `/ingest` | `backend/routers/inventory_ops.py` |
| GET | `/intel` | `backend/routers/security_ops.py` |
| POST | `/query` | `backend/routers/inventory_ops.py` |
| POST | `/reload` | `backend/routers/admin_ops.py` |
| GET | `/tia/summary` | `backend/routers/inventory_ops.py` |
| GET | `/timeline/minimal` | `backend/routers/security_ops.py` |
| GET | `/v1/system/status` | `backend/routers/system_ops.py` |

## Repo statistics

- Files scanned: **65**
- Python files: **49**
- Syntax errors: **0**
- Missing baseline files: **0**
- Undocumented secret-shaped env vars: **0**
- Stray files: **0**

## Known gaps

_None detected by the automated scan._

## Librarian handshake

- RAG corpus: [`librarian/rag_corpus.jsonl`](./rag_corpus.jsonl)
- Gap report: [`librarian/gap_report.json`](./gap_report.json)
- Schema: [`librarian/README.md`](./README.md)
- Status endpoint: `GET /api/v1/system/status` (also at `/v1/system/status` for cross-node parity)

