import time
from collections import defaultdict

class RequestsDetector:
    def __init__(self, limit=3, window=10):
        self.attempts = defaultdict(list)
        self.banned_ips = set()

    async def scan(self, ip, engine):
        if ip in self.banned_ips: return False
        now = time.time()
        self.attempts[ip] = [t for t in self.attempts[ip] if now - t < 10]
        if len(self.attempts[ip]) >= 3:
            self.banned_ips.add(ip)
            await engine.execute_websocket_kill()
            return False
        self.attempts[ip].append(now)
        return True
