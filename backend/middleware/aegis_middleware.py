"""
FastAPI middleware for Aegis IP monitoring
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
import secrets

from backend.security.ip_monitor import aegis_monitor

logger = logging.getLogger(__name__)

async def aegis_auth_middleware(request: Request, call_next):
    """
    Middleware to enforce IP monitoring and authentication checks.
    
    Checks:
    1. IP not banned
    2. AEGIS_COMMANDER_TOKEN valid (if required endpoint)
    """
    # Extract client IP
    client_ip = request.client.host
    
    # Check if IP is banned
    if not aegis_monitor.check_ip_allowed(client_ip):
        return JSONResponse(
            status_code=403,
            content={"error": "IP address banned due to security violations"}
        )
    
    # Check for protected endpoints
    if request.url.path.startswith('/api/v1/admin') or request.url.path.startswith('/api/v1/trade'):
        # Verify AEGIS_COMMANDER_TOKEN
        token = request.headers.get('Authorization')
        expected_token = os.getenv('AEGIS_COMMANDER_TOKEN')
        
        # Use constant-time comparison to prevent timing attacks
        token_valid = False
        if token and expected_token:
            provided_token = token.replace('Bearer ', '')
            token_valid = secrets.compare_digest(provided_token, expected_token)
        
        if not token_valid:
            # Record auth failure
            aegis_monitor.record_auth_failure(client_ip, failure_type="invalid_token")
            
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing authentication token"}
            )
    
    # Process request
    response = await call_next(request)
    return response
