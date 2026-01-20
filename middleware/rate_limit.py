"""
Rate limiting middleware for FastAPI
Implements token-based rate limiting for authenticated users
"""
import logging
import time
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from ..utils.rate_limiter import rate_limit_check, default_rate_limiter
from fastapi import Request

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    """
    Rate limiting middleware that uses authentication data to identify users
    """

    def __init__(self, max_requests: int = 10, window_size: int = 60):
        """
        Initialize rate limiting middleware

        Args:
            max_requests: Maximum number of requests allowed per window
            window_size: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        # We'll use the default rate limiter with custom parameters
        self.rate_limiter = default_rate_limiter

    async def __call__(self, request: Request, user_data: Dict[str, Any]) -> None:
        """
        Check if request is allowed based on rate limiting

        Args:
            request: FastAPI request object
            user_data: User data from authentication

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Extract user identifier from user data
        user_id = user_data.get("user", {}).get("id") or user_data.get("userId") or user_data.get("sub")

        if not user_id:
            # If we can't identify the user, use IP address as fallback
            client_host = request.client.host if request.client else "unknown"
            user_id = f"ip_{client_host}"

        # Check if request is allowed
        allowed = await rate_limit_check(user_id, self.rate_limiter)

        if not allowed:
            remaining_requests = self.rate_limiter.get_remaining_requests(user_id)
            reset_time = self.rate_limiter.get_reset_time(user_id)
            retry_after = int(reset_time - time.time())

            logger.warning(f"Rate limit exceeded for user {user_id}")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit is {self.max_requests} requests per {self.window_size} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": str(0),
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(retry_after)
                }
            )

        # Add rate limit headers to response
        remaining_requests = self.rate_limiter.get_remaining_requests(user_id)
        reset_time = self.rate_limiter.get_reset_time(user_id)

        # Store rate limit info in request state for response headers
        request.state.rate_limit_remaining = remaining_requests
        request.state.rate_limit_reset = int(reset_time)
        request.state.rate_limit_limit = self.max_requests


# For use as a dependency in endpoints that require rate limiting
async def apply_rate_limit(request: Request, user_data: Dict[str, Any]) -> None:
    """
    Rate limiting dependency for FastAPI endpoints
    """
    middleware = RateLimitMiddleware(max_requests=10, window_size=60)
    await middleware(request, user_data)