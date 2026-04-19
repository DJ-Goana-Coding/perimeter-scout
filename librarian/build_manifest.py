#!/usr/bin/env python3
"""
Librarian manifest / RAG corpus / gap report generator.

Walks the repository working tree and produces three artifacts in
``librarian/``:

* ``MANIFEST.md``      — human-readable summary
* ``rag_corpus.jsonl`` — machine-readable RAG corpus (one JSON record per line)
* ``gap_report.json``  — machine-readable findings (syntax errors, missing
                         baseline files, undocumented secret references,
                         stray files)

The script intentionally uses only the Python standard library so it can run
in a minimal CI environment without ``pip install``.

Schema details are documented in ``librarian/README.md``.
"""

from __future__ import annotations

import ast
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARIAN_DIR = REPO_ROOT / "librarian"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Files we expect every node to ship. Missing entries become gap_report rows.
EXPECTED_FILES: List[Tuple[str, str]] = [
    ("README.md", "Top-level project documentation."),
    ("requirements.txt", "Python dependency manifest."),
    ("Dockerfile", "Container build definition for HF Space deployment."),
    (".gitignore", "Standard ignore rules."),
    ("backend/main.py", "FastAPI application entrypoint."),
]

# Directories never indexed.
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "data", "dist", "build", ".idea",
    ".vscode",
}

# File suffixes we treat as binary and skip.
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tgz", ".whl",
    ".so", ".dylib", ".dll", ".class", ".jar", ".ico", ".woff", ".woff2",
    ".ttf", ".otf", ".mp4", ".mov", ".webm", ".bin", ".pkl",
}

# Files we never index regardless of suffix.
SKIP_FILES = {".DS_Store"}

# Soft chunking thresholds (bytes of text).
CHUNK_THRESHOLD = 8 * 1024
CHUNK_TARGET = 6 * 1024

# Heuristic regex for env-var-style secret references in source.
SECRET_REF_RE = re.compile(
    r"""(?:os\.getenv\(\s*|os\.environ(?:\.get)?\(\s*|os\.environ\[\s*)
        ['"]([A-Z][A-Z0-9_]{2,})['"]""",
    re.VERBOSE,
)

# Names matching this pattern are treated as "secret-shaped" and must be
# documented somewhere (README, librarian/MANIFEST, .env.example, etc.) or
# they show up in gap_report.undocumented_secrets.
SECRET_NAME_HINTS = re.compile(
    r"(TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL|API|AUTH)", re.IGNORECASE
)

# Where we look for documentation evidence of a secret.
DOC_SEARCH_FILES = [
    "README.md", "SECURITY.md", ".env.example", "librarian/MANIFEST.md",
    "docs",
]

LANG_BY_SUFFIX = {
    ".py": "python", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml",
    ".json": "json", ".sh": "shell", ".toml": "toml", ".ini": "ini",
    ".cfg": "ini", ".txt": "text", ".html": "html", ".css": "css",
    ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".jsx": "javascript", ".dockerfile": "dockerfile",
}

# Tag heuristics: substring (lowercased) -> tag.
PATH_TAG_HINTS: List[Tuple[str, str]] = [
    ("aegis", "aegis"),
    ("perimeter_scout", "perimeter-scout"),
    ("admiral", "admiral"),
    ("admirai", "admirai"),
    ("mapping_inventory", "mapping-inventory"),
    ("inventory", "inventory"),
    ("drive", "drive"),
    ("streamlit", "streamlit"),
    ("router", "router"),
    ("middleware", "middleware"),
    ("detector", "detector"),
    ("interceptor", "interceptor"),
    ("security", "security"),
    ("workflow", "ci"),
    (".github", "ci"),
    ("docker", "docker"),
    ("librarian", "librarian"),
    ("docs", "docs"),
    ("test", "test"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_name() -> str:
    return REPO_ROOT.name


def _iter_files() -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        # in-place prune
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name in SKIP_FILES:
                continue
            p = Path(dirpath) / name
            if p.suffix.lower() in BINARY_SUFFIXES:
                continue
            yield p


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _detect_language(path: Path) -> str:
    if path.name == "Dockerfile":
        return "dockerfile"
    return LANG_BY_SUFFIX.get(path.suffix.lower(), "text")


def _derive_tags(path: Path, language: str) -> List[str]:
    rel = path.relative_to(REPO_ROOT).as_posix().lower()
    tags = {language}
    for needle, tag in PATH_TAG_HINTS:
        if needle in rel:
            tags.add(tag)
    if rel.endswith("main.py"):
        tags.add("entrypoint")
    if "fastapi" in (rel + " "):
        tags.add("fastapi")
    return sorted(tags)


def _derive_title(path: Path, text: str) -> str:
    # Markdown: first H1.
    if path.suffix.lower() == ".md":
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    # Python: module docstring.
    if path.suffix.lower() == ".py":
        try:
            tree = ast.parse(text)
            doc = ast.get_docstring(tree)
            if doc:
                first = doc.strip().splitlines()[0].strip()
                if first:
                    return first[:120]
        except SyntaxError:
            pass
    # Generic: first non-empty, non-shebang, non-comment line.
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#!"):
            continue
        cleaned = s.lstrip("#/* -").strip()
        if cleaned:
            return cleaned[:120]
    return path.name


def _derive_summary(path: Path, text: str, title: str) -> str:
    if path.suffix.lower() == ".py":
        try:
            tree = ast.parse(text)
            doc = ast.get_docstring(tree)
            if doc:
                return " ".join(doc.split())[:280]
        except SyntaxError:
            pass
    if path.suffix.lower() == ".md":
        # First paragraph after the title.
        paras = re.split(r"\n\s*\n", text.strip())
        for p in paras:
            p = p.strip()
            if p.startswith("#") or not p:
                continue
            return " ".join(p.split())[:280]
    return title[:280]


def _chunk(text: str) -> List[str]:
    if len(text.encode("utf-8")) <= CHUNK_THRESHOLD:
        return [text]
    chunks: List[str] = []
    buf: List[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        line_size = len(line.encode("utf-8"))
        if size + line_size > CHUNK_TARGET and buf:
            chunks.append("".join(buf))
            buf = [line]
            size = line_size
        else:
            buf.append(line)
            size += line_size
    if buf:
        chunks.append("".join(buf))
    return chunks


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------


def _collect_secret_refs(py_files: List[Tuple[Path, str]]) -> Dict[str, List[str]]:
    refs: Dict[str, List[str]] = {}
    for path, text in py_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for match in SECRET_REF_RE.finditer(text):
            name = match.group(1)
            refs.setdefault(name, [])
            if rel not in refs[name]:
                refs[name].append(rel)
    return refs


def _gather_doc_corpus() -> str:
    parts: List[str] = []
    for entry in DOC_SEARCH_FILES:
        p = REPO_ROOT / entry
        if p.is_file():
            t = _read_text(p)
            if t:
                parts.append(t)
        elif p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file() and sub.suffix.lower() in {".md", ".txt"}:
                    t = _read_text(sub)
                    if t:
                        parts.append(t)
    return "\n".join(parts)


def _find_undocumented_secrets(
    secret_refs: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    if not secret_refs:
        return []
    docs = _gather_doc_corpus()
    out: List[Dict[str, Any]] = []
    for name, locations in sorted(secret_refs.items()):
        if not SECRET_NAME_HINTS.search(name):
            # Not secret-shaped; treated as ordinary config.
            continue
        documented_in: List[str] = []
        if name in docs:
            documented_in.append("docs")
        if not documented_in:
            out.append({
                "name": name,
                "found_in": locations,
                "documented_in": documented_in,
            })
    return out


def _check_syntax(py_files: List[Tuple[Path, str]]) -> List[Dict[str, Any]]:
    errors: List[Dict[str, Any]] = []
    for path, text in py_files:
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            errors.append({
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "line": exc.lineno or 0,
                "message": (exc.msg or "syntax error")[:200],
            })
    return errors


def _check_expected(files: List[Path]) -> List[Dict[str, Any]]:
    present = {p.relative_to(REPO_ROOT).as_posix() for p in files}
    missing: List[Dict[str, Any]] = []
    for rel, reason in EXPECTED_FILES:
        if rel not in present:
            missing.append({"path": rel, "reason": reason})
    return missing


def _detect_stray_files(files: List[Path]) -> List[Dict[str, Any]]:
    stray: List[Dict[str, Any]] = []
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        # Files whose name looks like a pasted URL.
        if rel.lower().startswith("http") and rel.endswith(".txt"):
            stray.append({"path": rel, "reason": "Filename appears to be a pasted URL."})
    return stray


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------


def _enumerate_endpoints(py_files: List[Tuple[Path, str]]) -> List[Dict[str, str]]:
    """Find FastAPI route declarations in source for the manifest."""
    endpoints: List[Dict[str, str]] = []
    route_re = re.compile(
        r"@(?:[\w]+)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"
    )
    for path, text in py_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for m in route_re.finditer(text):
            endpoints.append({
                "method": m.group(1).upper(),
                "path": m.group(2),
                "source": rel,
            })
    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    return endpoints


def _enumerate_env_vars(py_files: List[Tuple[Path, str]]) -> List[str]:
    seen = set()
    for _, text in py_files:
        for m in SECRET_REF_RE.finditer(text):
            seen.add(m.group(1))
    return sorted(seen)


def _build_manifest_md(
    files: List[Path],
    py_files: List[Tuple[Path, str]],
    endpoints: List[Dict[str, str]],
    env_vars: List[str],
    gap: Dict[str, Any],
) -> str:
    repo = _repo_name()
    now = _now_iso()
    total = len(files)
    py_count = len(py_files)

    lines: List[str] = []
    a = lines.append
    a(f"# {repo} — Librarian Manifest")
    a("")
    a(f"_Generated: `{now}` by `librarian/build_manifest.py`._")
    a("")
    a("> **Source of truth for the Mapping & Inventory Librarian.** This "
      "file is regenerated on every push; do not hand-edit. To change the "
      "structure, edit `librarian/build_manifest.py`.")
    a("")
    a("## Purpose")
    a("")
    a("Perimeter Scout is the **Aegis Security Core** for the Pioneer "
      "Ecosystem. It exposes a FastAPI backend (with an optional Streamlit "
      "dashboard) that performs real-time posture intelligence, IP "
      "monitoring with auto-ban, and a battery of detectors (requests, "
      "auth, config, integrity, network, behavior). It also acts as a "
      "client of the Pioneer Trader **Mapping & Inventory** hub for fleet "
      "inventory, T.I.A. risk summaries, and RAG ingest/query proxying.")
    a("")
    a("## Module map")
    a("")
    a("| Path | Role |")
    a("|---|---|")
    a("| `backend/main.py` | FastAPI bootstrap, CORS, middleware, router registration. |")
    a("| `backend/core/` | Module registry, event bus, policy engine, module interface. |")
    a("| `backend/middleware/aegis_middleware.py` | IP-allow + `AEGIS_COMMANDER_TOKEN` gate. |")
    a("| `backend/security/ip_monitor.py` | Auto-ban after repeated auth failures. |")
    a("| `backend/routers/` | `security`, `modules`, `admin`, `inventory` HTTP routes. |")
    a("| `backend/services/perimeter_scout/` | Aegis core + detectors + interceptors. |")
    a("| `backend/services/admiral/` | Admiral trading engine stub. |")
    a("| `backend/services/admirai/` | Admirai orchestrator. |")
    a("| `backend/services/mapping_inventory/client.py` | HTTP client for the M&I hub. |")
    a("| `backend/services/agents/` | Agent base + TIA agent + future template. |")
    a("| `streamlit_app/app.py` | Streamlit dashboard. |")
    a("| `tasks/security_digest.py` | Daily security digest background task. |")
    a("| `utils/drive_auth.py` | Google Drive auth (stub). |")
    a("| `config/policy.aegis.json` | Aegis policy document loaded by the policy engine. |")
    a("| `librarian/` | This integration directory. |")
    a("")
    a("## External integrations")
    a("")
    a("- **Pioneer Trader Mapping & Inventory hub** (`PIONEER_TRADER_URL`): "
      "fleet inventory, cockpit health, TIA summary, RAG `/v1/ingest` and "
      "`/v1/query` proxy.")
    a("- **Citadel Nexus Faceplate (Vercel HUD)** "
      "(`https://citadel-nexus-private.vercel.app`): allowed CORS origin; "
      "consumes `/health/*` and `/api/v1/system/status`.")
    a("- **Hugging Face Space** (`huggingface.co/spaces/$HF_USERNAME/$HF_SPACE_NAME`): "
      "deployment target, mirrored by `.github/workflows/hf_sync.yml`.")
    a("- **Google Drive** (`utils/drive_auth.py`): stub today; intended "
      "Citadel folder sync via the CITADEL-BOT tunnel.")
    a("")
    a("## Environment variables")
    a("")
    if env_vars:
        a("| Variable | Referenced in |")
        a("|---|---|")
        # Re-derive locations for documentation.
        refs = _collect_secret_refs(py_files)
        for name in env_vars:
            locs = ", ".join(f"`{p}`" for p in refs.get(name, []))
            a(f"| `{name}` | {locs or '—'} |")
    else:
        a("_No environment variables referenced._")
    a("")
    a("## HTTP endpoints")
    a("")
    if endpoints:
        a("> Note: routers are mounted with `prefix='/api/v1'` in "
          "`backend/main.py`, so `/security/...` becomes `/api/v1/security/...` "
          "in production.")
        a("")
        a("| Method | Path (in source) | Source file |")
        a("|---|---|---|")
        for ep in endpoints:
            a(f"| {ep['method']} | `{ep['path']}` | `{ep['source']}` |")
    else:
        a("_No endpoints discovered._")
    a("")
    a("## Repo statistics")
    a("")
    a(f"- Files scanned: **{total}**")
    a(f"- Python files: **{py_count}**")
    a(f"- Syntax errors: **{len(gap['syntax_errors'])}**")
    a(f"- Missing baseline files: **{len(gap['missing_expected_files'])}**")
    a(f"- Undocumented secret-shaped env vars: **{len(gap['undocumented_secrets'])}**")
    a(f"- Stray files: **{len(gap['stray_files'])}**")
    a("")
    a("## Known gaps")
    a("")
    if any(gap[k] for k in ("syntax_errors", "missing_expected_files",
                             "undocumented_secrets", "stray_files")):
        for key in ("syntax_errors", "missing_expected_files",
                    "undocumented_secrets", "stray_files"):
            items = gap[key]
            if not items:
                continue
            a(f"### {key.replace('_', ' ').title()}")
            a("")
            for item in items:
                a(f"- `{json.dumps(item, sort_keys=True)}`")
            a("")
    else:
        a("_None detected by the automated scan._")
    a("")
    a("## Librarian handshake")
    a("")
    a("- RAG corpus: [`librarian/rag_corpus.jsonl`](./rag_corpus.jsonl)")
    a("- Gap report: [`librarian/gap_report.json`](./gap_report.json)")
    a("- Schema: [`librarian/README.md`](./README.md)")
    a(f"- Status endpoint: `GET /api/v1/system/status` (also at `/v1/system/status` for cross-node parity)")
    a("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    files = sorted(_iter_files())
    py_files: List[Tuple[Path, str]] = []
    for p in files:
        if p.suffix.lower() == ".py":
            t = _read_text(p)
            if t is not None:
                py_files.append((p, t))

    gap = {
        "repo": _repo_name(),
        "generated_at": _now_iso(),
        "summary": {},
        "syntax_errors": _check_syntax(py_files),
        "missing_expected_files": _check_expected(files),
        "undocumented_secrets": _find_undocumented_secrets(
            _collect_secret_refs(py_files)
        ),
        "stray_files": _detect_stray_files(files),
    }
    gap["summary"] = {
        "files_scanned": len(files),
        "python_files": len(py_files),
        "syntax_errors": len(gap["syntax_errors"]),
        "missing_expected_files": len(gap["missing_expected_files"]),
        "undocumented_secrets": len(gap["undocumented_secrets"]),
        "stray_files": len(gap["stray_files"]),
    }

    endpoints = _enumerate_endpoints(py_files)
    env_vars = _enumerate_env_vars(py_files)

    LIBRARIAN_DIR.mkdir(parents=True, exist_ok=True)

    # Write gap_report.json
    # Note: gap["undocumented_secrets"] contains env-variable *names*
    # (e.g. "AEGIS_COMMANDER_TOKEN") harvested from os.getenv() calls in
    # source code, not the values of those variables. The Librarian needs
    # the names surfaced so the operator can document or remove them. No
    # process environment is read here, so there is no secret to leak.
    (LIBRARIAN_DIR / "gap_report.json").write_text(
        json.dumps(gap, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )

    # Write rag_corpus.jsonl
    repo = _repo_name()
    now = _now_iso()
    corpus_path = LIBRARIAN_DIR / "rag_corpus.jsonl"
    with corpus_path.open("w", encoding="utf-8") as fh:
        for p in files:
            rel = p.relative_to(REPO_ROOT).as_posix()
            # Skip the artifacts the script itself produces, to avoid the
            # corpus indexing yesterday's corpus.
            if rel in {"librarian/rag_corpus.jsonl",
                       "librarian/gap_report.json",
                       "librarian/MANIFEST.md"}:
                continue
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            text = _read_text(p)
            if text is None:
                continue
            sha = _sha256_bytes(raw)
            language = _detect_language(p)
            tags = _derive_tags(p, language)
            title = _derive_title(p, text)
            summary = _derive_summary(p, text, title)
            chunks = _chunk(text)
            for idx, chunk in enumerate(chunks):
                rec = {
                    "id": (f"{repo}::{rel}" if len(chunks) == 1
                           else f"{repo}::{rel}#{idx}"),
                    "repo": repo,
                    "path": rel,
                    "sha": sha,
                    "title": title,
                    "tags": tags,
                    "summary": summary,
                    "content_chunk": chunk,
                    "chunk_index": idx,
                    "chunk_total": len(chunks),
                    "language": language,
                    "size_bytes": len(raw),
                    "generated_at": now,
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Write MANIFEST.md
    md = _build_manifest_md(files, py_files, endpoints, env_vars, gap)
    (LIBRARIAN_DIR / "MANIFEST.md").write_text(md, encoding="utf-8")

    print(f"Wrote {len(files)} file scan results.")
    print(f"  rag_corpus.jsonl entries: see file ({corpus_path})")
    print(f"  gap summary: {json.dumps(gap['summary'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
