---
title: Perimeter Scout
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
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

The app runs as a Docker container on port **7860**.  
Set the `PIONEER_TRADER_URL` secret in your Space settings to connect to the Pioneer Trader backend.
