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

### Quick Deploy to Hugging Face Spaces

1. **Create a new Space** at https://huggingface.co/new-space
   - Select **Docker** as the SDK
   - Set the app port to **7860**

2. **Push this repository to your Space**:
   ```bash
   # Add Hugging Face as a remote (replace YOUR_USERNAME and SPACE_NAME)
   git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME

   # Push to Hugging Face
   git push huggingface main
   ```

3. **Configure Secrets** in your Space settings:
   - `PIONEER_TRADER_URL` - URL of the Pioneer Trader mapping-and-inventory backend
   - `AEGIS_COMMANDER_TOKEN` - (Optional) Authentication token for admin endpoints

4. **Connect to mapping-and-inventory**:
   - The `PIONEER_TRADER_URL` environment variable connects Perimeter Scout to the Pioneer Trader backend
   - Default endpoints:
     - `/api/v1/inventory/fleet` - Fleet inventory
     - `/api/v1/inventory/health` - Cockpit health
     - `/api/v1/inventory/tia/summary` - T.I.A. risk summary

### Verifying the Connection

Once deployed, test the mapping-and-inventory connection:
```bash
curl https://YOUR_SPACE.hf.space/api/v1/inventory/health
```
