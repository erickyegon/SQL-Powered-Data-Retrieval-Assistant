"""
Database utilities for Advanced SQL Assistant
Provides database schema analysis, query validation, and performance monitoring
"""

import re
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime, timedelta

from config import (
    BLOCKED_SQL_KEYWORDS, ALLOWED_SQL_KEYWORDS,
    ENABLE_SQL_VALIDATION, QUERY_TIMEOUT_SECONDS,
    LOG_QUERIES, LOG_PERFORMANCE
)

# Setup logging
logger = logging.getLogger(__name__)


class DatabaseAnalyzer:
    """Comprehensive database analysis and monitoring"""

    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self.query_stats = []

    def get_comprehensive_schema(self) -> Dict[str, Any]:
        """Get comprehensive database schema information"""
        try:
            self.metadata.reflect(bind=self.engine)

            schema_info = {
                'database_type': self.engine.dialect.name,
                'tables': {},
                'relationships': [],
                'indexes': {},
                'constraints': {},
                'statistics': {}
            }

            # Analyze each table
            for table_name in self.inspector.get_table_names():
                table_info = self._analyze_table(table_name)
                schema_info['tables'][table_name] = table_info

                # Get indexes
                indexes = self.inspector.get_indexes(table_name)
                schema_info['indexes'][table_name] = indexes

                # Get foreign keys (relationships)
                foreign_keys = self.inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    schema_info['relationships'].append({
                        'from_table': table_name,
                        'from_columns': fk['constrained_columns'],
                        'to_table': fk['referred_table'],
                        'to_columns': fk['referred_columns']
                    })

            # Get database statistics
            schema_info['statistics'] = self._get_database_statistics()

            return schema_info

        except Exception as e:
            logger.error(f"Error getting comprehensive schema: {e}")
            return {'error': str(e)}

    def _analyze_table(self, table_name: str) -> Dict[str, Any]:
        """Analyze individual table structure and statistics"""
        try:
            columns = self.inspector.get_columns(table_name)
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            unique_constraints = self.inspector.get_unique_constraints(
                table_name)
            check_constraints = self.inspector.get_check_constraints(
                table_name)

            # Get row count and basic statistics
            with self.engine.connect() as conn:
                try:
                    row_count_result = conn.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = row_count_result.scalar()
                except:
                    row_count = "Unknown"

            table_info = {
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': col.get('default'),
                        'autoincrement': col.get('autoincrement', False)
                    }
                    for col in columns
                ],
                'primary_key': pk_constraint.get('constrained_columns', []),
                'unique_constraints': unique_constraints,
                'check_constraints': check_constraints,
                'row_count': row_count,
                'estimated_size': self._estimate_table_size(table_name)
            }

            return table_info

        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {e}")
            return {'error': str(e)}

    def _estimate_table_size(self, table_name: str) -> str:
        """Estimate table size (database-specific)"""
        try:
            with self.engine.connect() as conn:
                if self.engine.dialect.name == 'mysql':
                    query = """
                    SELECT 
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() AND table_name = :table_name
                    """
                    result = conn.execute(
                        text(query), {'table_name': table_name})
                    size = result.scalar()
                    return f"{size} MB" if size else "Unknown"

                elif self.engine.dialect.name == 'postgresql':
                    query = """
                    SELECT pg_size_pretty(pg_total_relation_size(:table_name)) AS size
                    """
                    result = conn.execute(
                        text(query), {'table_name': table_name})
                    return result.scalar() or "Unknown"

                else:
                    return "Unknown"

        except Exception as e:
            logger.error(f"Error estimating table size for {table_name}: {e}")
            return "Unknown"

    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        try:
            stats = {
                'total_tables': len(self.inspector.get_table_names()),
                'total_views': len(self.inspector.get_view_names()),
                'database_size': self._get_database_size(),
                'last_analyzed': datetime.now().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {'error': str(e)}

    def _get_database_size(self) -> str:
        """Get total database size"""
        try:
            with self.engine.connect() as conn:
                if self.engine.dialect.name == 'mysql':
                    query = """
                    SELECT 
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE()
                    """
                    result = conn.execute(text(query))
                    size = result.scalar()
                    return f"{size} MB" if size else "Unknown"

                elif self.engine.dialect.name == 'postgresql':
                    query = "SELECT pg_size_pretty(pg_database_size(current_database())) AS size"
                    result = conn.execute(text(query))
                    return result.scalar() or "Unknown"

                else:
                    return "Unknown"

        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return "Unknown"

    def suggest_optimizations(self) -> List[Dict[str, str]]:
        """Suggest database optimizations based on analysis"""
        suggestions = []

        try:
            schema = self.get_comprehensive_schema()

            for table_name, table_info in schema.get('tables', {}).items():
                # Check for missing primary keys
                if not table_info.get('primary_key'):
                    suggestions.append({
                        'type': 'missing_primary_key',
                        'table': table_name,
                        'suggestion': f"Consider adding a primary key to table '{table_name}' for better performance",
                        'priority': 'high'
                    })

                # Check for large tables without indexes
                if (isinstance(table_info.get('row_count'), int) and
                        table_info['row_count'] > 10000):

                    table_indexes = schema.get(
                        'indexes', {}).get(table_name, [])
                    if len(table_indexes) < 2:  # Only primary key
                        suggestions.append({
                            'type': 'missing_indexes',
                            'table': table_name,
                            'suggestion': f"Large table '{table_name}' ({table_info['row_count']} rows) may benefit from additional indexes",
                            'priority': 'medium'
                        })

                # Check for tables with many columns (potential normalization issue)
                if len(table_info.get('columns', [])) > 20:
                    suggestions.append({
                        'type': 'normalization',
                        'table': table_name,
                        'suggestion': f"Table '{table_name}' has {len(table_info['columns'])} columns - consider normalization",
                        'priority': 'low'
                    })

            # Check for orphaned relationships
            relationships = schema.get('relationships', [])
            if len(relationships) == 0 and len(schema.get('tables', {})) > 1:
                suggestions.append({
                    'type': 'relationships',
                    'table': 'multiple',
                    'suggestion': "No foreign key relationships found - consider adding them for data integrity",
                    'priority': 'medium'
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return [{'type': 'error', 'suggestion': f'Error analyzing database: {e}', 'priority': 'high'}]


class QueryValidator:
    """SQL query validation and security checking"""

    @staticmethod
    def validate_sql_query(query: str) -> Tuple[bool, List[str]]:
        """Validate SQL query for security and compliance"""
        if not ENABLE_SQL_VALIDATION:
            return True, []

        errors = []
        warnings = []

        # Check for blocked keywords
        query_upper = query.upper()
        for keyword in BLOCKED_SQL_KEYWORDS:
            if keyword in query_upper:
                errors.append(f"Blocked keyword '{keyword}' found in query")

        # Check for SQL injection patterns
        injection_patterns = [
            r"';.*--",  # Comment injection
            r"UNION.*SELECT",  # Union injection
            r"OR.*1=1",  # Always true condition
            r"DROP.*TABLE",  # Table dropping
            r"INSERT.*INTO",  # Data insertion
            r"UPDATE.*SET",  # Data update
            r"DELETE.*FROM"  # Data deletion
        ]

        for pattern in injection_patterns:
            if re.search(pattern, query_upper):
                errors.append(
                    f"Potential SQL injection pattern detected: {pattern}")

        # Check query complexity
        complexity_warnings = QueryValidator._check_query_complexity(query)
        warnings.extend(complexity_warnings)

        # Check for performance issues
        performance_warnings = QueryValidator._check_performance_issues(query)
        warnings.extend(performance_warnings)

        return len(errors) == 0, errors + warnings

    @staticmethod
    def _check_query_complexity(query: str) -> List[str]:
        """Check for overly complex queries"""
        warnings = []
        query_upper = query.upper()

        # Count subqueries
        subquery_count = query_upper.count('SELECT') - 1
        if subquery_count > 3:
            warnings.append(
                f"Complex query with {subquery_count} subqueries may be slow")

        # Count joins
        join_count = query_upper.count('JOIN')
        if join_count > 5:
            warnings.append(
                f"Query has {join_count} joins which may impact performance")

        # Check for cartesian products
        if 'JOIN' not in query_upper and query_upper.count('FROM') > 1:
            warnings.append(
                "Potential cartesian product detected - consider using explicit JOINs")

        return warnings

    @staticmethod
    def _check_performance_issues(query: str) -> List[str]:
        """Check for common performance issues"""
        warnings = []
        query_upper = query.upper()

        # Check for SELECT *
        if 'SELECT *' in query_upper:
            warnings.append(
                "Using SELECT * may impact performance - consider specifying columns")

        # Check for missing LIMIT on large operations
        if ('GROUP BY' in query_upper or 'ORDER BY' in query_upper) and 'LIMIT' not in query_upper:
            warnings.append(
                "Consider adding LIMIT clause for better performance")

        # Check for functions in WHERE clause
        function_patterns = ['UPPER(', 'LOWER(', 'SUBSTRING(', 'DATE(']
        where_clause = query_upper.split(
            'WHERE')[1:] if 'WHERE' in query_upper else []
        for clause in where_clause:
            for func in function_patterns:
                if func in clause:
                    warnings.append(
                        f"Function {func.rstrip('(')} in WHERE clause may prevent index usage")
                    break

        return warnings


class QueryPerformanceMonitor:
    """Monitor and analyze query performance"""

    def __init__(self):
        self.query_logs = []
        self.performance_metrics = {}

    def execute_with_monitoring(self, engine, query: str) -> Tuple[Any, Dict[str, Any]]:
        """Execute query with performance monitoring"""
        start_time = time.time()

        try:
            with engine.connect() as conn:
                # Get execution plan first
                explain_query = self._get_explain_query(
                    query, engine.dialect.name)
                explain_result = None

                if explain_query:
                    try:
                        explain_result = conn.execute(
                            text(explain_query)).fetchall()
                    except:
                        pass  # Explain might fail for some queries

                # Execute actual query
                result = conn.execute(text(query))
                rows = result.fetchall()
                columns = result.keys()

                execution_time = time.time() - start_time

                # Log performance metrics
                metrics = {
                    'query': query,
                    'execution_time': execution_time,
                    'rows_returned': len(rows),
                    'columns_returned': len(columns),
                    'timestamp': datetime.now(),
                    'explain_plan': explain_result
                }

                if LOG_PERFORMANCE:
                    self.query_logs.append(metrics)
                    logger.info(
                        f"Query executed in {execution_time:.3f}s, returned {len(rows)} rows")

                return (rows, columns), metrics

        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            error_metrics = {
                'query': query,
                'execution_time': execution_time,
                'error': str(e),
                'timestamp': datetime.now()
            }

            if LOG_PERFORMANCE:
                self.query_logs.append(error_metrics)
                logger.error(f"Query failed after {execution_time:.3f}s: {e}")

            raise e

    def _get_explain_query(self, query: str, dialect: str) -> Optional[str]:
        """Get appropriate EXPLAIN query for database dialect"""
        if dialect == 'mysql':
            return f"EXPLAIN FORMAT=JSON {query}"
        elif dialect == 'postgresql':
            return f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
        else:
            return None

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_logs = [log for log in self.query_logs
                       if log.get('timestamp', datetime.min) > cutoff_time]

        if not recent_logs:
            return {'message': 'No queries in specified time period'}

        # Calculate statistics
        execution_times = [log['execution_time'] for log in recent_logs
                           if 'execution_time' in log and 'error' not in log]

        summary = {
            'total_queries': len(recent_logs),
            'successful_queries': len(execution_times),
            'failed_queries': len(recent_logs) - len(execution_times),
            'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'total_rows_returned': sum(log.get('rows_returned', 0) for log in recent_logs),
            'time_period_hours': hours,
            'generated_at': datetime.now().isoformat()
        }

        # Find slowest queries
        slow_queries = sorted(recent_logs,
                              key=lambda x: x.get('execution_time', 0),
                              reverse=True)[:5]
        summary['slowest_queries'] = [
            {
                'query': log['query'][:100] + '...' if len(log['query']) > 100 else log['query'],
                'execution_time': log.get('execution_time', 0),
                'rows_returned': log.get('rows_returned', 0)
            }
            for log in slow_queries if 'error' not in log
        ]

        return summary

    def clear_logs(self, older_than_hours: int = 24):
        """Clear old performance logs"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        self.query_logs = [log for log in self.query_logs
                           if log.get('timestamp', datetime.now()) > cutoff_time]


class DatabaseConnectionManager:
    """Manage database connections and health monitoring"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None
        self.last_health_check = None
        self.health_status = {'status': 'unknown', 'last_check': None}

    def get_engine(self):
        """Get database engine with lazy initialization"""
        if self.engine is None:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=LOG_QUERIES
            )
        return self.engine

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            engine = self.get_engine()
            start_time = time.time()

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            response_time = time.time() - start_time

            self.health_status = {
                'status': 'healthy',
                'response_time': response_time,
                'last_check': datetime.now().isoformat(),
                'database_type': engine.dialect.name
            }

            self.last_health_check = datetime.now()

        except Exception as e:
            self.health_status = {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

        return self.health_status

    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        if self.engine is None:
            return {'status': 'not_connected'}

        try:
            info = {
                'database_type': self.engine.dialect.name,
                'driver': self.engine.dialect.driver,
                'server_version': None,
                'connection_pool_size': self.engine.pool.size(),
                'checked_out_connections': self.engine.pool.checkedout(),
                'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
            }

            # Get server version
            try:
                with self.engine.connect() as conn:
                    if self.engine.dialect.name == 'mysql':
                        result = conn.execute(text("SELECT VERSION()"))
                        info['server_version'] = result.scalar()
                    elif self.engine.dialect.name == 'postgresql':
                        result = conn.execute(text("SELECT version()"))
                        info['server_version'] = result.scalar()
            except:
                pass

            return info

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

# Utility functions


def create_database_analyzer(engine) -> DatabaseAnalyzer:
    """Factory function to create database analyzer"""
    return DatabaseAnalyzer(engine)


def validate_query(query: str) -> Tuple[bool, List[str]]:
    """Convenience function for query validation"""
    return QueryValidator.validate_sql_query(query)


def create_performance_monitor() -> QueryPerformanceMonitor:
    """Factory function to create performance monitor"""
    return QueryPerformanceMonitor()


def create_connection_manager(connection_string: str) -> DatabaseConnectionManager:
    """Factory function to create connection manager"""
    return DatabaseConnectionManager(connection_string)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    print("Database utilities module loaded successfully")

    # Test query validation
    test_queries = [
        "SELECT * FROM users;",
        "DROP TABLE users;",  # Should be blocked
        "SELECT id, name FROM users WHERE active = 1;",
        "SELECT * FROM users; DROP TABLE users;",  # Should be blocked
    ]

    for query in test_queries:
        is_valid, messages = validate_query(query)
        print(f"Query: {query[:50]}...")
        print(f"Valid: {is_valid}")
        if messages:
            print(f"Messages: {messages}")
        print("-" * 50)
