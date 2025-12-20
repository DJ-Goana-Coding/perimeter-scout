import json
import os
from datetime import datetime

LOG_PATH = "data/warlord_minimal.log"  # keep name if already used; file is local-only
os.makedirs("data", exist_ok=True)

_last_posture = None


def minilog(posture_block):
    global _last_posture
    current = posture_block.get("posture", "UNKNOWN")

    if current == _last_posture:
        return

    _last_posture = current
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "posture": current,
        "tags": posture_block.get("tags", []),
    }

    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
