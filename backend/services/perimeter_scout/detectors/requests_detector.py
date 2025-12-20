from typing import Dict, Any


class RequestsDetector:
    async def run(self) -> Dict[str, Any]:
        return {
            "status": "OK",
            "message": "Request volume normal",
        }
