from typing import Dict, Any
from ...core.policy_engine import PolicyEngine
from ...core.module_registry import ModuleRegistry


class Admirai:
    VERSION = "0.1.0"

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
        self.policy = PolicyEngine()

    def version(self):
        return self.VERSION

    def capabilities(self):
        return ["orchestration", "policy_engine"]

    async def get_status(self) -> Dict[str, Any]:
        return {
            "modules": self.registry.list(),
            "capabilities": self.registry.capabilities(),
        }

    async def system_brief(self) -> Dict[str, Any]:
        perimeter = self.registry.get("perimeter_scout")
        if not perimeter:
            return {"error": "Perimeter Scout (Aegis) not available"}

        aegis_status = await perimeter.get_status()
        policy_actions = self.policy.evaluate(aegis_status)

        return {
            "posture": aegis_status,
            "policy_actions": policy_actions,
        }
