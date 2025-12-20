from typing import Dict, Any
from .base_agent import FutureAgent


class FutureAgentTemplate(FutureAgent):
    VERSION = "1.0.0"

    def version(self):
        return self.VERSION

    def capabilities(self):
        return ["analysis", "template_agent"]

    async def consume_aegis(self, tia_snapshot: Dict[str, Any]):
        self.snapshot = tia_snapshot

    async def produce_summary(self) -> Dict[str, Any]:
        return {
            "summary": "Template agent summary",
            "risk_level": "LOW",
            "confidence": 1.0,
        }
