# Perimeter Scout — Integrity Audit

**Date:** 2026-04-18
**Branch:** `copilot/stability-9293-token-validation`
**Scope:** `backend/`, `tasks/`, `streamlit_app/`, `utils/`

## 1. Method

A static AST-based import scan was run over every `.py` file in the four
trees above. For each `Import` / `ImportFrom` node:

- Relative imports were resolved against the file's package path and
  checked against the set of internal modules actually present on disk.
- Absolute imports were classified against the Python standard library
  (`sys.stdlib_module_names`) and the project's declared third-party
  dependencies in `requirements.txt`
  (`fastapi`, `uvicorn`, `requests`, `streamlit`, `pandas`, `plotly`,
  plus their transitive runtime imports `pydantic` / `starlette`).
- Anything not matching any of those buckets was reported as
  `UNRESOLVED_ABS` / `UNRESOLVED_REL` / `REL_TOO_DEEP`.

## 2. Files scanned

```
backend/         24 .py files (core, routers, services/*, security, middleware)
tasks/            2 .py files (security_digest, __init__)
streamlit_app/    1 .py file  (app)
utils/            2 .py files (drive_auth, __init__)
```

## 3. Findings

**Unresolved imports: 0**
**Parse errors: 0**
**Orphan / dangling relative imports: 0**

The tree is internally consistent. No artefacts from previous
Termux/Laptop sessions (e.g. dangling `from harvest...`,
`from rag_local...`, or absolute paths into `/sdcard/...`) were found.

## 4. Cross-checks performed

- `python -c "import backend.main"` — succeeds; the FastAPI app builds
  and the full router set registers without error.
- Route enumeration confirms the new RAG proxy endpoints are mounted at
  the expected paths:
    - `POST /api/v1/inventory/ingest`
    - `POST /api/v1/inventory/query`
  alongside the pre-existing
    - `GET  /api/v1/inventory/fleet`
    - `GET  /api/v1/inventory/health`
    - `GET  /api/v1/inventory/tia/summary`

## 5. Changes shipped in this audit pass

| Area | Change | Reason |
| --- | --- | --- |
| `README.md` | HF front-matter `app_port: 7860` → `8000` | Match the backend standard declared in `docker-compose.yml` and prevent the Space from binding to a port the container does not listen on ("Grey Space"). |
| `start.sh` | Default `PORT` `7860` → `8000` | Make the container actually listen on the port the HF manifest advertises. |
| `Dockerfile` | `EXPOSE` reordered so `8000` is primary | Consistency only; HF ignores `EXPOSE` but local tooling reads it. |
| `backend/services/mapping_inventory/client.py` | Added `_post()`, `ingest_document()`, `query_index()` | Thin proxy onto the hub's `/v1/ingest` and `/v1/query`. The hub owns the global FAISS store; this spoke does not hold index state. |
| `backend/routers/inventory_ops.py` | Added `POST /ingest`, `POST /query` | Spoke-side surface for the RAG hub-and-spoke link, mounted under the existing `/api/v1/inventory` group. |
| `data/master_harvest/.gitkeep` | New file | Local ingestion-buffer placeholder for Master Harvest fragments. |

## 6. Items deliberately *not* changed

- The HF Space `Authorization: Bearer ${HF_TOKEN}` flow in
  `.github/workflows/hf_sync.yml` was not touched. Token presence /
  validity is enforced by the workflow itself (`Verify HF_TOKEN is
  configured` step) and is not visible to a sandboxed agent.
- No FAISS dependency was added to `requirements.txt`. The vector store
  lives on the hub by design; adding `faiss-cpu` here would create a
  second index and contradict the hub-and-spoke model.
- No "Master Harvest" content was fabricated. The `data/master_harvest/`
  directory is empty by intent — it is the inbound buffer, not a
  generated corpus.

## 7. Status

`9,293 Stability` — confirmed for the audited surface.
No unresolved imports, no orphan modules, no parse failures, RAG spoke
endpoints registered, HF Space port aligned with container.
