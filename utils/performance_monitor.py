"""
Performance monitoring utility for tracking response times and system metrics
"""
import time
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import threading
import statistics
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class to hold performance metrics"""
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class PerformanceMonitor:
    """
    Performance monitoring class to track response times and system metrics
    """
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.active_requests: Dict[str, PerformanceMetrics] = {}
        self.completed_requests: deque = deque(maxlen=max_samples)
        self.lock = threading.Lock()

        # Track metrics by endpoint
        self.endpoint_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))

    def start_request(self, request_id: str, endpoint: str, user_id: Optional[str] = None) -> PerformanceMetrics:
        """Start monitoring a request"""
        with self.lock:
            start_time = time.time()
            metrics = PerformanceMetrics(
                request_id=request_id,
                start_time=start_time,
                endpoint=endpoint,
                user_id=user_id
            )
            self.active_requests[request_id] = metrics
            return metrics

    def end_request(self, request_id: str, status: str = "success", error: Optional[str] = None) -> Optional[PerformanceMetrics]:
        """End monitoring a request and record metrics"""
        with self.lock:
            if request_id not in self.active_requests:
                logger.warning(f"Request {request_id} not found in active requests")
                return None

            metrics = self.active_requests[request_id]
            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time
            metrics.status = status
            metrics.error = error

            # Add to completed requests
            self.completed_requests.append(metrics)

            # Add to endpoint-specific metrics
            if metrics.endpoint:
                self.endpoint_metrics[metrics.endpoint].append(metrics)

            # Remove from active requests
            del self.active_requests[request_id]

            # Log performance metrics
            logger.info(f"Request {request_id} completed in {metrics.duration:.3f}s - {status}")

            return metrics

    def get_average_response_time(self, endpoint: Optional[str] = None, last_n: int = 100) -> Optional[float]:
        """Get average response time for an endpoint or overall"""
        with self.lock:
            if endpoint:
                metrics_list = list(self.endpoint_metrics[endpoint])
            else:
                metrics_list = list(self.completed_requests)

            # Get last N metrics
            recent_metrics = metrics_list[-min(last_n, len(metrics_list)):]

            if not recent_metrics:
                return None

            durations = [m.duration for m in recent_metrics if m.duration is not None]
            if not durations:
                return None

            return statistics.mean(durations)

    def get_p95_response_time(self, endpoint: Optional[str] = None, last_n: int = 100) -> Optional[float]:
        """Get 95th percentile response time for an endpoint or overall"""
        with self.lock:
            if endpoint:
                metrics_list = list(self.endpoint_metrics[endpoint])
            else:
                metrics_list = list(self.completed_requests)

            # Get last N metrics
            recent_metrics = metrics_list[-min(last_n, len(metrics_list)):]

            if not recent_metrics:
                return None

            durations = [m.duration for m in recent_metrics if m.duration is not None]
            if not durations:
                return None

            durations.sort()
            index = int(0.95 * len(durations))
            if index >= len(durations):
                index = len(durations) - 1

            return durations[index]

    def get_active_request_count(self) -> int:
        """Get count of currently active requests"""
        with self.lock:
            return len(self.active_requests)

    def get_total_requests_count(self) -> int:
        """Get total count of completed requests"""
        with self.lock:
            return len(self.completed_requests)

    def get_error_rate(self, endpoint: Optional[str] = None, last_n: int = 100) -> float:
        """Get error rate for an endpoint or overall"""
        with self.lock:
            if endpoint:
                metrics_list = list(self.endpoint_metrics[endpoint])
            else:
                metrics_list = list(self.completed_requests)

            # Get last N metrics
            recent_metrics = metrics_list[-min(last_n, len(metrics_list)):]

            if not recent_metrics:
                return 0.0

            error_count = sum(1 for m in recent_metrics if m.status == "error" or m.error is not None)
            return error_count / len(recent_metrics)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class PerformanceTimer:
    """
    Context manager and decorator for timing function execution
    """
    def __init__(self, name: str, request_id: Optional[str] = None, endpoint: Optional[str] = None, user_id: Optional[str] = None):
        self.name = name
        self.request_id = request_id
        self.endpoint = endpoint
        self.user_id = user_id
        self.metrics: Optional[PerformanceMetrics] = None

    def __enter__(self):
        self.metrics = performance_monitor.start_request(
            request_id=self.request_id or f"timer_{time.time()}",
            endpoint=self.endpoint or self.name,
            user_id=self.user_id
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "success"
        error_msg = str(exc_val) if exc_val else None
        performance_monitor.end_request(self.metrics.request_id, status, error_msg)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)


def monitor_performance(name: str, endpoint: Optional[str] = None):
    """
    Decorator for monitoring function performance
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with PerformanceTimer(name, endpoint=endpoint):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with PerformanceTimer(name, endpoint=endpoint):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


# Convenience functions
def start_performance_monitoring(request_id: str, endpoint: str, user_id: Optional[str] = None) -> PerformanceMetrics:
    """Start performance monitoring for a request"""
    return performance_monitor.start_request(request_id, endpoint, user_id)


def end_performance_monitoring(request_id: str, status: str = "success", error: Optional[str] = None) -> Optional[PerformanceMetrics]:
    """End performance monitoring for a request"""
    return performance_monitor.end_request(request_id, status, error)


def get_performance_stats(endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    return {
        "average_response_time": performance_monitor.get_average_response_time(endpoint),
        "p95_response_time": performance_monitor.get_p95_response_time(endpoint),
        "active_requests": performance_monitor.get_active_request_count(),
        "total_requests": performance_monitor.get_total_requests_count(),
        "error_rate": performance_monitor.get_error_rate(endpoint),
        "timestamp": datetime.utcnow().isoformat()
    }