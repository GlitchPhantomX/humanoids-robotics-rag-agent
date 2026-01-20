"""
Rate limiting utility for API endpoints
Implements token-based rate limiting with sliding window algorithm
"""
import time
import threading
from typing import Dict, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Sliding window rate limiter that tracks requests per user
    """

    def __init__(self, max_requests: int = 10, window_size: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests: Maximum number of requests allowed per window
            window_size: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests: Dict[str, deque] = {}
        self.lock = threading.Lock()

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if a request from user_id is allowed

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if request is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()

            # Initialize request history for new users
            if user_id not in self.requests:
                self.requests[user_id] = deque()

            # Remove requests that are outside the current window
            request_queue = self.requests[user_id]
            while request_queue and current_time - request_queue[0] > self.window_size:
                request_queue.popleft()

            # Check if we've exceeded the limit
            if len(request_queue) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return False

            # Add current request to the queue
            request_queue.append(current_time)
            return True

    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get number of remaining requests for user in current window

        Args:
            user_id: Unique identifier for the user

        Returns:
            Number of remaining requests
        """
        with self.lock:
            current_time = time.time()

            if user_id not in self.requests:
                return self.max_requests

            request_queue = self.requests[user_id]
            # Remove requests that are outside the current window
            while request_queue and current_time - request_queue[0] > self.window_size:
                request_queue.popleft()

            return self.max_requests - len(request_queue)

    def get_reset_time(self, user_id: str) -> float:
        """
        Get time when rate limit will reset for user

        Args:
            user_id: Unique identifier for the user

        Returns:
            Unix timestamp when rate limit will reset
        """
        with self.lock:
            current_time = time.time()

            if user_id not in self.requests:
                return current_time

            request_queue = self.requests[user_id]
            # Remove requests that are outside the current window
            while request_queue and current_time - request_queue[0] > self.window_size:
                request_queue.popleft()

            if not request_queue:
                return current_time

            # Reset time is the time of the oldest request + window_size
            return request_queue[0] + self.window_size

# Global rate limiter instance
default_rate_limiter = RateLimiter(max_requests=10, window_size=60)

async def rate_limit_check(user_id: str, rate_limiter: RateLimiter = None) -> bool:
    """
    Async wrapper for rate limiting check

    Args:
        user_id: Unique identifier for the user
        rate_limiter: Rate limiter instance (uses default if None)

    Returns:
        True if request is allowed, False otherwise
    """
    if rate_limiter is None:
        rate_limiter = default_rate_limiter

    return rate_limiter.is_allowed(user_id)