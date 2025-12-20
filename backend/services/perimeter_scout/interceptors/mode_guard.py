from typing import Dict, Any, List


class ModeGuardInterceptor:
    async def evaluate(self, intel: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
