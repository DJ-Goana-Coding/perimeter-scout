# Aegis Forensic Shield - Security System

## Overview

The Aegis Forensic Shield is an automated IP monitoring and threat response system that protects the Perimeter Scout infrastructure from unauthorized access attempts.

## Features

### 1. **IP Monitoring & Auto-Ban System**
- Real-time tracking of authentication failures per IP address
- Automatic ban after **3 failed attempts** within 10 minutes
- **24-hour ban duration** for malicious IPs
- Forensic logging of all security events

### 2. **FastAPI Middleware Integration**
- Transparent request interception and IP verification
- Token-based authentication for protected endpoints
- HTTP 403 Forbidden responses for banned IPs
- HTTP 401 Unauthorized for invalid authentication

### 3. **Daily Security Digest**
- Automated daily reports generated at midnight UTC
- Comprehensive statistics on security events
- Optional Google Drive upload for audit trails
- 7-day event retention with automatic cleanup

### 4. **Health Monitoring**
- `/health/security` endpoint for real-time status
- Reports banned IP count and daily statistics
- Public endpoint for monitoring tools

## Architecture

```
┌─────────────────┐
│  Client Request │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Aegis Middleware       │
│  - Check IP ban status  │
│  - Verify token auth    │
└────────┬────────────────┘
         │
         ├─ Banned? → 403 Forbidden
         ├─ Invalid token? → Record failure → 401 Unauthorized
         │                    │
         │                    ▼ (3 failures)
         │              ┌──────────────┐
         │              │  Auto-ban IP │
         │              └──────────────┘
         │
         ▼
┌─────────────────┐
│  API Endpoint   │
└─────────────────┘
```

## Configuration

### Environment Variables

```bash
# Required for protected endpoints (/api/admin, /api/trade)
export AEGIS_COMMANDER_TOKEN="your-secret-token-here"
```

### Protected Endpoints

The following endpoint prefixes require authentication:
- `/api/admin/*` - Administrative operations
- `/api/trade/*` - Trading operations

### Public Endpoints

These endpoints are accessible without authentication:
- `/health/security` - Security status
- `/api/v1/security/*` - Security intelligence
- `/api/v1/modules/*` - Module information

## Usage

### Starting the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set authentication token
export AEGIS_COMMANDER_TOKEN="your-secret-token"

# Start the server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Making Authenticated Requests

```bash
# Protected endpoint - requires token
curl -H "Authorization: Bearer your-secret-token" \
  http://localhost:8000/api/admin/reload

# Security health check - no token required
curl http://localhost:8000/health/security
```

## Security Features

### 1. **Constant-Time Token Comparison**
Uses `secrets.compare_digest()` to prevent timing attacks when verifying authentication tokens.

### 2. **IP-Based Rate Limiting**
- Tracks failures per IP in a 10-minute sliding window
- Automatic ban after threshold exceeded
- 24-hour ban duration

### 3. **Forensic Logging**
All security events are logged with:
- Timestamp (ISO 8601 format)
- IP address
- Event type (auth_failure, auto_ban)
- Failure reason

### 4. **Path Traversal Prevention**
Filenames are sanitized using `os.path.basename()` to prevent directory traversal attacks.

## Monitoring

### Daily Security Digest

Example digest format:
```json
{
  "date": "2026-02-09",
  "total_events": 15,
  "auth_failures": 12,
  "auto_bans": 3,
  "unique_ips": 5,
  "currently_banned": 2,
  "events": [...]
}
```

### Health Endpoint Response

```json
{
  "status": "operational",
  "aegis_version": "3.1.0",
  "banned_ips_count": 2,
  "today_events": 15,
  "today_bans": 3
}
```

## Testing

### Manual Testing

```bash
# Test auto-ban (3 failed attempts)
for i in {1..3}; do
  curl http://localhost:8000/api/admin/reload
  sleep 1
done

# This request should be blocked
curl http://localhost:8000/api/admin/reload
# Expected: {"error": "IP address banned due to security violations"}
```

### Functional Tests

```python
from backend.security.ip_monitor import AegisMonitor

monitor = AegisMonitor(max_failures=3, ban_duration_hours=24)

# Test IP allowed initially
assert monitor.check_ip_allowed("192.168.1.100") == True

# Record failures
for _ in range(3):
    monitor.record_auth_failure("192.168.1.100")

# IP should now be banned
assert monitor.check_ip_allowed("192.168.1.100") == False
```

## Troubleshooting

### Issue: All requests are being blocked

**Solution:** Check if your IP was auto-banned due to repeated failures. Bans expire after 24 hours, or restart the server to clear the ban list.

### Issue: Protected endpoints not requiring authentication

**Solution:** Ensure the endpoint path starts with `/api/admin` or `/api/trade`. Other paths are not protected by default.

### Issue: Token authentication failing

**Solution:** Verify the `AEGIS_COMMANDER_TOKEN` environment variable is set correctly and matches the token in your request header.

## Future Enhancements

Potential improvements for production deployments:

1. **Distributed State Management**
   - Use Redis for shared ban list across multiple instances
   - Persistent storage for security events

2. **Advanced Analytics**
   - Geographic IP analysis
   - Attack pattern detection
   - Anomaly detection using ML

3. **Integration Enhancements**
   - Slack/Discord notifications for security events
   - Webhook support for SIEM integration
   - Real-time dashboard

4. **Google Drive Integration**
   - Complete implementation with service account auth
   - Automated report upload and archival

## Support

For issues or questions about the Aegis Forensic Shield:
- Review logs for security events
- Check `/health/security` endpoint for current status
- Contact the security team for ban list management

---

**Version:** 3.1.0  
**Last Updated:** February 2026  
**Security Level:** MAXIMUM
