"""
Logging and error handling utilities for Advanced SQL Assistant
Provides comprehensive logging, error tracking, and monitoring capabilities
"""

import logging
import traceback
import functools
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import streamlit as st

from config import LOG_LEVEL, LOG_QUERIES, LOG_PERFORMANCE


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class StructuredLogger:
    """Structured logging with JSON output for advanced analysis"""

    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler for structured logs
        if log_file:
            self._setup_file_logging(log_file)

        self.session_id = self._generate_session_id()

    def _setup_file_logging(self, log_file: str):
        """Setup file logging with rotation"""
        try:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup file logging: {e}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def log_structured(self, level: str, message: str, **kwargs):
        """Log structured data with additional context"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'message': message,
            'level': level.upper(),
            **kwargs
        }

        # Log as string for console
        getattr(self.logger, level.lower())(message)

        # Store structured data if needed
        if hasattr(self, '_structured_logs'):
            self._structured_logs.append(log_data)

    def log_query(self, query: str, execution_time: float, rows_returned: int, **kwargs):
        """Log SQL query execution"""
        if LOG_QUERIES:
            self.log_structured(
                'info',
                f"Query executed in {execution_time:.3f}s, returned {rows_returned} rows",
                query=query[:200] + "..." if len(query) > 200 else query,
                execution_time=execution_time,
                rows_returned=rows_returned,
                query_type='sql_execution',
                **kwargs
            )

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        if LOG_PERFORMANCE:
            self.log_structured(
                'info',
                f"Performance: {operation} took {duration:.3f}s",
                operation=operation,
                duration=duration,
                metric_type='performance',
                **kwargs
            )

    def log_error(self, error: Exception, context: str = None, **kwargs):
        """Log error with full context"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context
        }

        self.log_structured(
            'error',
            f"Error in {context or 'unknown context'}: {error}",
            **error_data,
            **kwargs
        )

    def log_user_action(self, action: str, details: Dict[str, Any] = None):
        """Log user actions for analytics"""
        self.log_structured(
            'info',
            f"User action: {action}",
            action=action,
            details=details or {},
            event_type='user_action'
        )


class ErrorTracker:
    """Track and analyze application errors"""

    def __init__(self):
        self.errors = []
        self.error_counts = {}
        self.logger = StructuredLogger('error_tracker')

    def track_error(self, error: Exception, context: str = None, user_query: str = None):
        """Track error occurrence with context"""
        error_info = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_query': user_query,
            'traceback': traceback.format_exc()
        }

        self.errors.append(error_info)

        # Update error counts
        error_key = f"{error_info['error_type']}:{error_info['context']}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Log error
        self.logger.log_error(error, context, user_query=user_query)

        # Keep only recent errors (last 24 hours)
        self._cleanup_old_errors()

    def _cleanup_old_errors(self, hours: int = 24):
        """Remove old error records"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.errors = [error for error in self.errors
                       if error['timestamp'] > cutoff_time]

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [error for error in self.errors
                         if error['timestamp'] > cutoff_time]

        if not recent_errors:
            return {'message': 'No errors in specified time period'}

        # Count errors by type
        error_types = {}
        for error in recent_errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Count errors by context
        error_contexts = {}
        for error in recent_errors:
            context = error['context'] or 'unknown'
            error_contexts[context] = error_contexts.get(context, 0) + 1

        return {
            'total_errors': len(recent_errors),
            'unique_error_types': len(error_types),
            'error_types': error_types,
            'error_contexts': error_contexts,
            'most_recent_error': recent_errors[-1] if recent_errors else None,
            'time_period_hours': hours,
            'generated_at': datetime.now().isoformat()
        }

    def get_recommendations(self) -> List[str]:
        """Get error-based recommendations"""
        recommendations = []
        error_summary = self.get_error_summary()

        if error_summary.get('total_errors', 0) == 0:
            return ["No recent errors - system is running smoothly!"]

        # Check for database connection issues
        if any('connection' in error_type.lower() for error_type in error_summary.get('error_types', {})):
            recommendations.append(
                "Database connection issues detected. Check network connectivity and credentials.")

        # Check for query syntax errors
        if any('syntax' in error_type.lower() for error_type in error_summary.get('error_types', {})):
            recommendations.append(
                "SQL syntax errors detected. Review query generation prompts and validation.")

        # Check for timeout issues
        if any('timeout' in error_type.lower() for error_type in error_summary.get('error_types', {})):
            recommendations.append(
                "Query timeout errors detected. Consider optimizing slow queries or increasing timeout limits.")

        # Check for authentication errors
        if any('auth' in error_type.lower() for error_type in error_summary.get('error_types', {})):
            recommendations.append(
                "Authentication errors detected. Verify API keys and database credentials.")

        # General recommendation based on error frequency
        total_errors = error_summary.get('total_errors', 0)
        if total_errors > 10:
            recommendations.append(
                f"High error rate detected ({total_errors} errors). Consider reviewing system health.")

        return recommendations or ["Review error logs for specific issues."]


class PerformanceMonitor:
    """Monitor application performance and resource usage"""

    def __init__(self):
        self.metrics = []
        self.logger = StructuredLogger('performance_monitor')

    def record_metric(self, metric_name: str, value: float, unit: str = 'seconds', **kwargs):
        """Record a performance metric"""
        metric = {
            'timestamp': datetime.now(),
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            **kwargs
        }

        self.metrics.append(metric)

        if LOG_PERFORMANCE:
            self.logger.log_performance(
                metric_name, value, unit=unit, **kwargs)

        # Keep only recent metrics
        self._cleanup_old_metrics()

    def _cleanup_old_metrics(self, hours: int = 24):
        """Remove old metric records"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.metrics = [metric for metric in self.metrics
                        if metric['timestamp'] > cutoff_time]

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [metric for metric in self.metrics
                          if metric['timestamp'] > cutoff_time]

        if not recent_metrics:
            return {'message': 'No metrics in specified time period'}

        # Group metrics by name
        metric_groups = {}
        for metric in recent_metrics:
            name = metric['metric_name']
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(metric['value'])

        # Calculate statistics for each metric
        metric_stats = {}
        for name, values in metric_groups.items():
            metric_stats[name] = {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'total': sum(values)
            }

        return {
            'total_metrics': len(recent_metrics),
            'metric_types': len(metric_groups),
            'metric_statistics': metric_stats,
            'time_period_hours': hours,
            'generated_at': datetime.now().isoformat()
        }

# Decorators for automatic logging and error handling


def log_execution_time(operation_name: str = None):
    """Decorator to log function execution time"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = StructuredLogger(func.__module__)

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                op_name = operation_name or f"{func.__name__}"
                logger.log_performance(op_name, execution_time)

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.log_error(
                    e, f"Function: {func.__name__}", execution_time=execution_time)
                raise

        return wrapper
    return decorator


def handle_errors(context: str = None, return_on_error: Any = None):
    """Decorator for consistent error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_tracker = get_global_error_tracker()
                error_tracker.track_error(e, context or func.__name__)

                if return_on_error is not None:
                    return return_on_error
                else:
                    raise

        return wrapper
    return decorator


def log_user_action(action_name: str = None):
    """Decorator to log user actions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger('user_actions')
            action = action_name or func.__name__

            # Extract relevant details from arguments
            details = {}
            if args:
                details['args_count'] = len(args)
            if kwargs:
                details['kwargs'] = {k: str(v)[:100]
                                     for k, v in kwargs.items()}

            logger.log_user_action(action, details)
            return func(*args, **kwargs)

        return wrapper
    return decorator


# Global instances for convenience
_global_error_tracker = None
_global_performance_monitor = None


def get_global_error_tracker() -> ErrorTracker:
    """Get global error tracker instance"""
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = ErrorTracker()
    return _global_error_tracker


def get_global_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor

# Streamlit-specific utilities


class StreamlitLogger:
    """Streamlit-specific logging utilities"""

    @staticmethod
    def display_error_summary():
        """Display error summary in Streamlit"""
        error_tracker = get_global_error_tracker()
        summary = error_tracker.get_error_summary()

        if 'message' in summary:
            st.success("✅ No recent errors")
        else:
            with st.expander("🚨 Error Summary", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Errors", summary.get('total_errors', 0))
                with col2:
                    st.metric("Error Types", summary.get(
                        'unique_error_types', 0))
                with col3:
                    st.metric("Time Period",
                              f"{summary.get('time_period_hours', 24)}h")

                if summary.get('error_types'):
                    st.subheader("Error Types")
                    for error_type, count in summary['error_types'].items():
                        st.write(f"• {error_type}: {count}")

                recommendations = error_tracker.get_recommendations()
                if recommendations:
                    st.subheader("Recommendations")
                    for rec in recommendations:
                        st.info(rec)

    @staticmethod
    def display_performance_summary():
        """Display performance summary in Streamlit"""
        perf_monitor = get_global_performance_monitor()
        summary = perf_monitor.get_performance_summary()

        if 'message' in summary:
            st.info("No performance metrics available")
        else:
            with st.expander("📊 Performance Summary", expanded=False):
                st.metric("Total Metrics", summary.get('total_metrics', 0))

                stats = summary.get('metric_statistics', {})
                if stats:
                    for metric_name, metric_stats in stats.items():
                        with st.container():
                            st.subheader(f"📈 {metric_name}")
                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric(
                                    "Average", f"{metric_stats['avg']:.3f}s")
                            with col2:
                                st.metric("Min", f"{metric_stats['min']:.3f}s")
                            with col3:
                                st.metric("Max", f"{metric_stats['max']:.3f}s")
                            with col4:
                                st.metric("Count", metric_stats['count'])

# Utility functions for common logging patterns


def log_query_execution(query: str, execution_time: float, rows_returned: int, **kwargs):
    """Convenience function for logging query execution"""
    logger = StructuredLogger('query_execution')
    logger.log_query(query, execution_time, rows_returned, **kwargs)


def log_llm_call(prompt: str, response: str, execution_time: float, model: str = None):
    """Log LLM API calls"""
    logger = StructuredLogger('llm_calls')
    logger.log_structured(
        'info',
        f"LLM call completed in {execution_time:.3f}s",
        prompt_length=len(prompt),
        response_length=len(response),
        execution_time=execution_time,
        model=model,
        event_type='llm_call'
    )


def track_user_session(action: str, details: Dict[str, Any] = None):
    """Track user session activities"""
    logger = StructuredLogger('user_session')
    logger.log_user_action(action, details)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    logger = StructuredLogger('test')
    error_tracker = get_global_error_tracker()
    perf_monitor = get_global_performance_monitor()

    # Test logging
    logger.log_structured('info', 'Test message', test_data={'key': 'value'})

    # Test error tracking
    try:
        raise ValueError("Test error")
    except Exception as e:
        error_tracker.track_error(e, 'test_context')

    # Test performance monitoring
    perf_monitor.record_metric('test_operation', 1.5, 'seconds')

    # Display summaries
    print("Error Summary:", error_tracker.get_error_summary())
    print("Performance Summary:", perf_monitor.get_performance_summary())

    print("Logging utilities module loaded successfully")
