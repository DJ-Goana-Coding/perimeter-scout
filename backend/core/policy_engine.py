import json
import os
from typing import Dict, Any, List

POLICY_PATH = "config/policy.aegis.json"


class PolicyEngine:
    def __init__(self, path: str = POLICY_PATH):
        self.path = path
        self.rules: list[dict] = []
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.rules = []
            return
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                self.rules = data.get("rules", [])
        except Exception:
            self.rules = []

    def evaluate(self, posture_block: Dict[str, Any]) -> List[Dict[str, Any]]:
        posture = posture_block.get("posture")
        tags = posture_block.get("tags", [])
        results: List[Dict[str, Any]] = []

        for rule in self.rules:
            cond = rule.get("when", {})
            match = True

            if "posture" in cond and cond["posture"] != posture:
                match = False

            if "tags_any" in cond:
                if not any(t in tags for t in cond["tags_any"]):
                    match = False

            if not match:
                continue

            for action in rule.get("actions", []):
                results.append(action)

        return results
