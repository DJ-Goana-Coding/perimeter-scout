# Librarian Integration

This directory is the **canonical handoff point** between this repository and
the **Mapping & Inventory Librarian** (the central RAG/index node for the
Citadel / Pioneer ecosystem).

Every repository in the ecosystem ships the same three artifacts in a
`librarian/` directory so the Librarian can ingest them with one consistent
crawler:

| Artifact | Purpose |
|---|---|
| `MANIFEST.md` | Human-readable repo summary: purpose, modules, endpoints, env vars, integrations, gaps. |
| `rag_corpus.jsonl` | Machine-readable RAG corpus. One JSON object per line, one record per file or file section. |
| `gap_report.json` | Machine-readable findings: missing files, syntax errors, undocumented secrets, dead imports. |

The artifacts are regenerated on every push to `main` by
`.github/workflows/librarian-build.yml`, which runs
[`librarian/build_manifest.py`](./build_manifest.py) and commits any changes
back to the repo. They are then mirrored to the Hugging Face Space by
`.github/workflows/hf_sync.yml`, so the Librarian can pull them either from
GitHub (via `GH_TOKEN`) or from the Space.

---

## `rag_corpus.jsonl` schema

One JSON object per line. Field order is not significant; every record MUST
include the following keys (additional keys are allowed):

```json
{
  "id": "perimeter-scout::backend/main.py",
  "repo": "perimeter-scout",
  "path": "backend/main.py",
  "sha": "sha256-of-content-as-hex",
  "title": "FastAPI application bootstrap",
  "tags": ["python", "fastapi", "entrypoint", "aegis"],
  "summary": "Wires CORS, Aegis middleware, module registry, and routers.",
  "content_chunk": "<the actual file/section text, possibly chunked>",
  "chunk_index": 0,
  "chunk_total": 1,
  "language": "python",
  "size_bytes": 4123,
  "generated_at": "2026-04-19T00:00:00Z"
}
```

Field meanings:

- **`id`** — globally unique. Format: `<repo>::<path>` (or
  `<repo>::<path>#<chunk_index>` if the file is chunked). The Librarian uses
  this as the primary key for deduplication.
- **`repo`** — short repo name, no owner prefix. Lets the Librarian filter
  per-node without parsing `id`.
- **`path`** — POSIX path, repo-root-relative.
- **`sha`** — `sha256` of the **raw file bytes** (not the chunk). Allows the
  Librarian to detect content changes without rechunking.
- **`title`** — short human label. Auto-generated from the first comment /
  docstring / heading when possible, falling back to the basename.
- **`tags`** — lower-case, deduplicated. Auto-derived from path, language,
  and well-known names (`aegis`, `fastapi`, `streamlit`, `mapping_inventory`,
  `drive`, `docker`, `ci`, etc.). Used for faceted retrieval.
- **`summary`** — 1–3 sentence purpose statement.
- **`content_chunk`** — the indexed text. Files larger than 8 KB are split
  into ~6 KB chunks on line boundaries; smaller files are emitted as a
  single chunk.
- **`chunk_index` / `chunk_total`** — 0-based chunk number and total chunk
  count for this file.
- **`language`** — best-effort language tag (`python`, `markdown`, `yaml`,
  `dockerfile`, `json`, `shell`, `text`).
- **`size_bytes`** — size of the **raw file**, not the chunk.
- **`generated_at`** — ISO-8601 UTC timestamp of when the record was built.

## `gap_report.json` schema

```json
{
  "repo": "perimeter-scout",
  "generated_at": "2026-04-19T00:00:00Z",
  "summary": {
    "files_scanned": 0,
    "python_files": 0,
    "syntax_errors": 0,
    "missing_expected_files": 0,
    "undocumented_secrets": 0
  },
  "syntax_errors": [
    {"path": "...", "line": 0, "message": "..."}
  ],
  "missing_expected_files": [
    {"path": "...", "reason": "..."}
  ],
  "undocumented_secrets": [
    {"name": "AEGIS_COMMANDER_TOKEN", "found_in": ["..."], "documented_in": ["README.md"]}
  ],
  "stray_files": [
    {"path": "...", "reason": "..."}
  ]
}
```

The Librarian reads `gap_report.json` to surface fixes ("missing app.py",
"undocumented secret", etc.) without re-scanning the codebase.

## How the Librarian consumes this

1. The Librarian's mapping crawler iterates over each repo it knows about
   (configured in its own `repos.yml`).
2. For each repo it does `GET .../librarian/rag_corpus.jsonl` and ingests
   every record into its FAISS index, keyed by `id`. Records with an
   unchanged `sha` are skipped.
3. It reads `gap_report.json` and merges the findings into the global
   gap-status board (used by the self-healing workflow to decide what to
   rebuild).
4. It reads `MANIFEST.md` for human-readable context surfaced in the Vercel
   HUD.

## Reusing this layout in another repo

Drop `librarian/build_manifest.py`, `librarian/README.md`, and the two
workflows (`librarian-build.yml`, `self-heal.yml`) into any sibling repo.
The script is repo-agnostic — it derives the repo name from the working
directory and walks whatever tree it finds. The only thing to adjust is the
`EXPECTED_FILES` list near the top of `build_manifest.py` if a particular
repo has different baseline expectations.

## Reproducing locally

```bash
python librarian/build_manifest.py
```

The script writes `librarian/MANIFEST.md`, `librarian/rag_corpus.jsonl`, and
`librarian/gap_report.json` in place. It uses only the Python standard
library, so no extra dependencies are required in CI.
