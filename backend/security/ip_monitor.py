"""
Aegis IP Monitor - Automated threat detection and response
Tracks authentication failures and auto-bans malicious IPs
"""
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AegisMonitor:
    """
    Real-time IP monitoring and threat response system.
    
    Features:
    - Track authentication failures per IP
    - Auto-ban after 3 failed attempts
    - Temporary ban duration: 24 hours
    - Forensic logging of all security events
    """
    
    def __init__(self, max_failures=3, ban_duration_hours=24):
        self.max_failures = max_failures
        self.ban_duration = timedelta(hours=ban_duration_hours)
        
        # Track failures per IP (IP -> deque of timestamps)
        self.failure_tracking = defaultdict(lambda: deque(maxlen=10))
        
        # Banned IPs (IP -> ban_expiry_time)
        self.banned_ips = {}
        
        # Security event log (for daily digest)
        self.security_events = []
    
    def check_ip_allowed(self, ip_address):
        """
        Check if IP is allowed to make requests.
        
        Args:
            ip_address: Client IP address
        
        Returns:
            bool: True if allowed, False if banned
        """
        # Check if IP is currently banned
        if ip_address in self.banned_ips:
            ban_expiry = self.banned_ips[ip_address]
            
            if datetime.now() < ban_expiry:
                logger.warning(f"🚫 BLOCKED REQUEST from banned IP: {ip_address}")
                return False
            else:
                # Ban expired, remove from list
                del self.banned_ips[ip_address]
                logger.info(f"✅ Ban expired for IP: {ip_address}")
        
        return True
    
    def record_auth_failure(self, ip_address, failure_type="invalid_token"):
        """
        Record an authentication failure and apply auto-ban if threshold exceeded.
        
        Args:
            ip_address: Client IP address
            failure_type: Type of authentication failure
        
        Returns:
            bool: True if IP was auto-banned, False otherwise
        """
        now = datetime.now()
        
        # Record failure
        self.failure_tracking[ip_address].append(now)
        
        # Log security event
        self.security_events.append({
            'timestamp': now.isoformat(),
            'ip': ip_address,
            'event': 'auth_failure',
            'type': failure_type
        })
        
        # Count recent failures (within last 10 minutes)
        recent_failures = sum(
            1 for ts in self.failure_tracking[ip_address]
            if now - ts < timedelta(minutes=10)
        )
        
        # Apply auto-ban if threshold exceeded
        if recent_failures >= self.max_failures:
            ban_expiry = now + self.ban_duration
            self.banned_ips[ip_address] = ban_expiry
            
            logger.critical(
                f"🔴 AUTO-BAN TRIGGERED: IP {ip_address} "
                f"({recent_failures} failures in 10 min) - "
                f"Banned until {ban_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Log ban event
            self.security_events.append({
                'timestamp': now.isoformat(),
                'ip': ip_address,
                'event': 'auto_ban',
                'failures': recent_failures,
                'ban_until': ban_expiry.isoformat()
            })
            
            return True
        
        logger.warning(
            f"⚠️ Auth failure for IP {ip_address} "
            f"({recent_failures}/{self.max_failures} strikes)"
        )
        
        return False
    
    def get_daily_summary(self):
        """
        Generate daily security summary.
        
        Returns:
            dict: Summary statistics
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Filter events from today
        today_events = [
            e for e in self.security_events
            if datetime.fromisoformat(e['timestamp']) >= today_start
        ]
        
        # Count by type
        auth_failures = sum(1 for e in today_events if e['event'] == 'auth_failure')
        auto_bans = sum(1 for e in today_events if e['event'] == 'auto_ban')
        
        # Unique IPs involved
        unique_ips = len(set(e['ip'] for e in today_events))
        
        summary = {
            'date': today_start.strftime('%Y-%m-%d'),
            'total_events': len(today_events),
            'auth_failures': auth_failures,
            'auto_bans': auto_bans,
            'unique_ips': unique_ips,
            'currently_banned': len(self.banned_ips),
            'events': today_events
        }
        
        return summary
    
    def clear_old_events(self, days_to_keep=7):
        """
        Clear security events older than specified days.
        
        Args:
            days_to_keep: Number of days of history to retain
        """
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        
        self.security_events = [
            e for e in self.security_events
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]

# Global monitor instance
# Note: In production deployments with multiple instances, consider using
# a distributed cache (Redis) or database for shared state management.
# For single-instance deployments, this global instance is sufficient.
aegis_monitor = AegisMonitor()
