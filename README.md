---
title: Perimeter Scout
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---

# 🛡️ Perimeter Scout — Aegis Security Core

**Perimeter Scout** is a security monitoring and intelligence dashboard for the Pioneer Ecosystem.  
It provides real-time threat detection, posture analysis, and integration with the **Mapping & Inventory** module from Pioneer Trader.

## Features

- **Aegis Security Core** — real-time posture intelligence (SAFE / WATCH / DANGER / CRITICAL)
- **IP Monitor** — auto-ban malicious IPs after repeated authentication failures
- **Detectors** — requests, auth, config, integrity, network, and behavior analysis
- **Mapping & Inventory** — live connection to Pioneer Trader fleet inventory and T.I.A. risk summaries
- **Module Event Bus** — cross-module event timeline
- **Policy Engine** — configurable security policy reload

## Architecture

```
perimeter-scout/
├─ backend/          # FastAPI backend
│  ├─ routers/       # API routes (security, modules, admin, inventory)
│  ├─ services/      # Aegis, Admiral, Admirai, Mapping-Inventory client
│  ├─ security/      # IP monitor and auto-ban
│  └─ middleware/    # Aegis auth middleware
├─ streamlit_app/    # Streamlit UI dashboard
├─ tasks/            # Background tasks (security digest)
└─ utils/            # Utilities (Drive auth)
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend (port 8000)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start the Streamlit frontend (port 8501)
streamlit run streamlit_app/app.py
```

## Docker

```bash
docker-compose up
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `API_BASE_URL` | Perimeter Scout backend URL | `http://localhost:8000/api/v1` |
| `PIONEER_TRADER_URL` | Pioneer Trader backend URL for mapping-and-inventory | `http://localhost:8001` |
| `AEGIS_COMMANDER_TOKEN` | Auth token for protected admin endpoints | *(none)* |

## Hugging Face Spaces Deployment

The app runs as a Docker container on port **8000** (matches the local
`backend/` standard and `docker-compose.yml`).
Set the `PIONEER_TRADER_URL` secret in your Space settings to connect to the Pioneer Trader backend.

## Librarian Integration

This repo ships a `librarian/` directory that the central **Mapping & Inventory Librarian** crawls to keep its RAG index in sync with this node. Three artifacts live there:

| Artifact | Purpose |
|---|---|
| [`librarian/MANIFEST.md`](./librarian/MANIFEST.md) | Human-readable repo summary: modules, endpoints, env vars, integrations, gaps. |
| [`librarian/rag_corpus.jsonl`](./librarian/rag_corpus.jsonl) | One JSON record per file/section, ready for direct ingestion into the Librarian's FAISS index. |
| [`librarian/gap_report.json`](./librarian/gap_report.json) | Machine-readable findings: syntax errors, missing baseline files, undocumented secrets, stray files. |

The schema is documented in [`librarian/README.md`](./librarian/README.md) and is identical across every node in the ecosystem so the Librarian's crawler is repo-agnostic.

### Cross-node telemetry endpoint

Every node exposes the same status contract (Phase 2.2 of the Universal Alignment Protocol):

```
GET /v1/system/status
GET /api/v1/system/status   # same payload, mounted under /api/v1 for parity
```

Returns `{repo, version, commit, uptime_seconds, modules, dependencies_ok, time}`. Unauthenticated and side-effect-free — safe for the Vercel HUD and the Librarian to poll cheaply.

### CORS

The CORS allowlist is configurable via the `ALLOWED_ORIGINS` environment variable (comma-separated). The defaults always include the Vercel HUD (`https://citadel-nexus-private.vercel.app`) and `localhost:3000` / `localhost:8501` for local development.

### CI / CD workflows

| Workflow | Trigger | Purpose | Secrets used |
|---|---|---|---|
| [`hf_sync.yml`](./.github/workflows/hf_sync.yml) | push to `main`, manual | Mirror the repo to the Hugging Face Space. Skips with a warning (no failure) if `HF_TOKEN` is missing. | `HF_TOKEN`, vars `HF_USERNAME`, `HF_SPACE_NAME` |
| [`librarian-build.yml`](./.github/workflows/librarian-build.yml) | push to `main`, manual | Regenerates the librarian artifacts and commits them back to `main`. | `GITHUB_TOKEN` (auto) |
| [`self-heal.yml`](./.github/workflows/self-heal.yml) | failure of either workflow above | Re-runs failed jobs once; opens (or comments on) a `librarian:node-failure` issue if the failure persists. | `GITHUB_TOKEN` (auto) |

### Required secrets

To enable Hugging Face sync, add the following under **Settings → Secrets and variables → Actions**:

- `HF_TOKEN` *(secret, required for HF sync — workflow skips cleanly if absent)* — Hugging Face access token with write scope on the target Space. Create at <https://huggingface.co/settings/tokens>.
- `HF_USERNAME` *(variable, optional)* — defaults to `DJ-Goana-Coding`.
- `HF_SPACE_NAME` *(variable, optional)* — defaults to `perimeter-scout`.

The application itself uses:

- `AEGIS_COMMANDER_TOKEN` — required to call `/api/v1/admin/*` and `/api/v1/trade/*`.
- `PIONEER_TRADER_URL` — Mapping & Inventory hub base URL (default `http://localhost:8001`).
- `API_BASE_URL` — Streamlit dashboard's backend URL (default `http://localhost:8000/api/v1`).
- `ALLOWED_ORIGINS` — extra CORS origins, comma-separated (optional).

### Regenerating the manifest locally

```bash
python librarian/build_manifest.py
```

Stdlib-only. Writes the three artifacts in place; commit them as part of normal development if you want a static snapshot, otherwise the CI workflow will keep them current automatically.
