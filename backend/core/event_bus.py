import json
import os
from datetime import datetime

EVENT_LOG_PATH = "data/module_events.log"
os.makedirs("data", exist_ok=True)


class EventBus:
    def __init__(self, path: str = EVENT_LOG_PATH):
        self.path = path

    def publish(self, module: str, event: str, tags=None):
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "module": module,
            "event": event,
            "tags": tags or [],
        }
        try:
            with open(self.path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            # Never break the system on logging
            pass

    def read(self, limit: int = 200):
        if not os.path.exists(self.path):
            return []
        events = []
        try:
            with open(self.path, "r") as f:
                for line in f.readlines()[-limit:]:
                    try:
                        events.append(json.loads(line))
                    except:
                        continue
        except Exception:
            return []
        return events
