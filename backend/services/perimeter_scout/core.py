from typing import Dict, Any
from .hound import Hound
from .perimeter_scout import PerimeterScout
from .ghost import Ghost
from .detectors.requests_detector import RequestsDetector
from .detectors.auth_detector import AuthDetector
from .detectors.config_detector import ConfigDetector
from .detectors.integrity_detector import IntegrityDetector
from .detectors.network_detector import NetworkDetector
from .detectors.behavior_detector import BehaviorDetector
from .interceptors.rate_limit import RateLimitInterceptor
from .interceptors.mode_guard import ModeGuardInterceptor
from .interceptors.lockout import LockoutInterceptor
from .minilog import minilog
from ...core.module_interface import ModuleInterface
from ...core.event_bus import EventBus


class AegisCore(ModuleInterface):
    VERSION = "1.0.0"

    def __init__(self, event_bus: EventBus | None = None):
        self.hound = Hound()
        self.perimeter_scout = PerimeterScout()
        self.ghost = Ghost()
        self.detectors = {
            "requests": RequestsDetector(),
            "auth": AuthDetector(),
            "config": ConfigDetector(),
            "integrity": IntegrityDetector(),
            "network": NetworkDetector(),
            "behavior": BehaviorDetector(),
        }
        self.interceptors = {
            "rate_limit": RateLimitInterceptor(),
            "mode_guard": ModeGuardInterceptor(),
            "lockout": LockoutInterceptor(),
        }
        self.event_bus = event_bus

    def version(self):
        return self.VERSION

    def capabilities(self):
        return [
            "intel.basic",
            "intel.tia_snapshot",
            "posture.model.v1",
            "recommendations.defensive",
        ]

    async def _collect_intel(self) -> Dict[str, Any]:
        hound_report = await self.hound.run_check()
        perimeter_report = await self.perimeter_scout.run_check()

        detectors_intel: Dict[str, Any] = {}
        for name, det in self.detectors.items():
            try:
                detectors_intel[name] = await det.run()
            except Exception as e:
                detectors_intel[name] = {
                    "status": "ERROR",
                    "message": str(e),
                }

        ghost_intel = await self.ghost.analyze(detectors_intel)
        posture_block = ghost_intel.get("posture", {})
        warnings = ghost_intel.get("warnings", [])

        intel = {
            "hound": hound_report,
            "perimeter": perimeter_report,
            "detectors": detectors_intel,
            "posture": posture_block,
            "warnings": warnings,
        }
        return intel

    async def deep_intel(self) -> Dict[str, Any]:
        intel = await self._collect_intel()
        posture_block = intel.get("posture", {})

        minilog(posture_block)

        if self.event_bus:
            self.event_bus.publish(
                module="perimeter_scout",
                event=f"posture:{posture_block.get('posture', 'UNKNOWN')}",
                tags=posture_block.get("tags", []),
            )

        return intel

    async def sample_intel(self) -> Dict[str, Any]:
        return await self.deep_intel()

    async def evaluate_and_intercept(self) -> Dict[str, Any]:
        intel = await self.deep_intel()
        posture_block = intel.get("posture", {})
        recommendations: list[dict] = []

        for name, interceptor in self.interceptors.items():
            try:
                recs = await interceptor.evaluate(intel)
                recommendations.extend(recs)
            except Exception:
                continue

        action_required = posture_block.get("posture") == "CRITICAL"

        return {
            "intel": intel,
            "recommendations": recommendations,
            "action_required": action_required,
        }

    # UMI methods

    async def get_intel(self):
        return await self.deep_intel()

    async def get_status(self):
        intel = await self.sample_intel()
        return intel.get("posture", {})

    async def get_recommendations(self):
        result = await self.evaluate_and_intercept()
        return result.get("recommendations", [])

    async def tia_snapshot(self) -> Dict[str, Any]:
        intel = await self.deep_intel()
        return {
            "posture": intel.get("posture", {}),
            "warnings": intel.get("warnings", []),
            "detector_status": {
                name: res.get("status", "UNKNOWN")
                for name, res in intel.get("detectors", {}).items()
            },
            "perimeter": {
                "dns_ok": intel["perimeter"].get("dns_ok"),
                "ssl_ok": intel["perimeter"].get("ssl_ok"),
                "latency_ms": intel["perimeter"].get("latency_ms"),
                "market_reachable": intel["perimeter"].get("market_reachable"),
            },
            "ghost": intel.get("posture", {}),
            "recommendations": [],
        }
