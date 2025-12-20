from typing import Dict, Any


class Ghost:
    async def analyze(self, detectors_intel: Dict[str, Any]) -> Dict[str, Any]:
        tags: list[str] = []
        posture = "SAFE"
        trajectory = "STABLE"
        warnings: list[str] = []

        for name, res in detectors_intel.items():
            status = res.get("status", "OK")
            if status in {"ALERT", "ERROR"}:
                posture = "DANGER"
                tags.append(f"{name.upper()}_ALERT")
                warnings.append(f"{name}: {res.get('message', 'Issue detected')}")

        return {
            "posture": {
                "posture": posture,
                "trajectory": trajectory,
                "tags": tags,
                "confidence": 1.0,
            },
            "warnings": warnings,
        }
