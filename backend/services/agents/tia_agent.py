from typing import Dict, Any
from .base_agent import FutureAgent


class TIAAgent(FutureAgent):
    VERSION = "1.0.0"

    def __init__(self):
        self.last_snapshot: Dict[str, Any] = {}

    def version(self):
        return self.VERSION

    def capabilities(self):
        return ["analysis", "tia_snapshot_consumer"]

    async def consume_aegis(self, tia_snapshot: Dict[str, Any]):
        self.last_snapshot = tia_snapshot

    async def produce_summary(self) -> Dict[str, Any]:
        posture = self.last_snapshot.get("posture", {})
        warnings = self.last_snapshot.get("warnings", [])
        detector_status = self.last_snapshot.get("detector_status", {})

        risk_level = "LOW"
        if posture.get("posture") in {"DANGER", "CRITICAL"}:
            risk_level = "HIGH"
        elif warnings:
            risk_level = "MEDIUM"

        return {
            "summary": f"System posture: {posture.get('posture', 'UNKNOWN')}",
            "risk_level": risk_level,
            "warnings": warnings,
            "detector_status": detector_status,
            "confidence": 0.9,
        }
