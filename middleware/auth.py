"""
Authentication validation middleware
Handles validation of user authentication for protected endpoints
"""
import logging
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security.http import HTTPBearer
import httpx
import os
from urllib.parse import urljoin

# Initialize logger
logger = logging.getLogger(__name__)

# Get auth backend URL from environment or use default
AUTH_BACKEND_URL = os.getenv("AUTH_BACKEND_URL", "http://localhost:8001")

class AuthValidator:
    """
    Authentication validation service with session timeout handling
    """

    def __init__(self, default_session_timeout: int = 3600):  # 1 hour default
        self.auth_backend_url = AUTH_BACKEND_URL
        self.default_session_timeout = default_session_timeout

    async def validate_session_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session token with auth backend and check for timeout
        Returns user data if valid and not timed out, None if invalid or timed out
        """
        try:
            # Construct the URL for session validation
            session_url = urljoin(self.auth_backend_url, "/api/auth/session")

            # Make request to auth backend to validate session
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    session_url,
                    headers={"Authorization": f"Bearer {session_token}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    session_data = response.json()
                    if session_data.get("isAuthenticated", False):
                        # Check if session has timed out based on last activity
                        if self._is_session_valid(session_data):
                            return session_data
                        else:
                            logger.info(f"Session timed out for user: {session_data.get('user', {}).get('id', 'unknown')}")
                            return None
                elif response.status_code == 401:
                    logger.info(f"Invalid session token: {session_token[:8]}...")
                    return None
                else:
                    logger.warning(f"Auth backend returned status {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error validating session token: {str(e)}")
            return None

        return None

    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """
        Check if session is still valid based on timeout
        """
        # Check if there's a last activity timestamp
        last_activity = session_data.get("lastActivity", session_data.get("createdAt"))

        if last_activity:
            # Convert timestamp to seconds if it's in milliseconds
            if isinstance(last_activity, (int, float)) and last_activity > 1e10:  # Likely in milliseconds
                last_activity = last_activity / 1000

            current_time = time.time()
            time_since_activity = current_time - last_activity

            # Check against timeout
            timeout = session_data.get("timeout", self.default_session_timeout)

            if time_since_activity > timeout:
                logger.debug(f"Session timed out after {time_since_activity:.2f}s (max: {timeout}s)")
                return False

        return True

    async def get_user_from_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract and validate user from request
        Checks both Authorization header and session cookie
        """
        # Check Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]  # Remove "Bearer " prefix
            return await self.validate_session_token(session_token)

        # Check for session cookie as fallback
        session_cookie = request.cookies.get("session_id") or request.cookies.get("session_token")
        if session_cookie:
            return await self.validate_session_token(session_cookie)

        return None

# Global instance with configurable timeout
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour default
auth_validator = AuthValidator(default_session_timeout=SESSION_TIMEOUT)

async def authenticate_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Authentication dependency for FastAPI endpoints
    Returns user data if authenticated, raises HTTPException if not
    """
    user_data = await auth_validator.get_user_from_request(request)

    if not user_data:
        logger.warning(f"Unauthenticated request to {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data

# For use as a dependency in endpoints that require authentication
auth_dependency = authenticate_request