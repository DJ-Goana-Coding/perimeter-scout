from typing import Dict, Any
from ...core.module_interface import ModuleInterface


class FutureAgent(ModuleInterface):
    async def consume_aegis(self, tia_snapshot: Dict[str, Any]):
        raise NotImplementedError

    async def produce_summary(self) -> Dict[str, Any]:
        raise NotImplementedError

    def capabilities(self):
        return ["analysis"]

    def version(self):
        return "1.0.0"
