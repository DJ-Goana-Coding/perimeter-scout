from typing import Dict, Any


class Hound:
    async def run_check(self) -> Dict[str, Any]:
        # Placeholder; later add real checks (heartbeat, latency, loop drift, etc.)
        return {
            "heartbeat_ok": True,
            "latency_ms": 42.0,
            "market_reachable": True,
            "loop_drift": False,
        }
