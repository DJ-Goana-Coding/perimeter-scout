from typing import Dict, Any


class AuthDetector:
    async def run(self) -> Dict[str, Any]:
        return {
            "status": "OK",
            "message": "Auth normal",
        }
