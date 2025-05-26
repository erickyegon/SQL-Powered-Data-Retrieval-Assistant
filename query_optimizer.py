"""
Advanced SQL Query Optimization Engine
Provides intelligent query analysis, optimization suggestions, and performance monitoring
"""

import re
import time
import json
import sqlparse
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from sqlalchemy import text, create_engine
from utils import call_groq_llm


class OptimizationLevel(Enum):
    """Optimization levels for different scenarios"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    execution_time: float
    rows_examined: int
    rows_returned: int
    memory_usage: float
    cpu_usage: float
    io_operations: int
    index_usage: Dict[str, bool]
    optimization_score: float


@dataclass
class OptimizationSuggestion:
    """Single optimization suggestion"""
    type: str
    priority: str  # HIGH, MEDIUM, LOW
    description: str
    sql_example: Optional[str]
    expected_improvement: str
    implementation_effort: str


class QueryAnalyzer:
    """Analyze SQL queries for optimization opportunities"""
    
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.db_type = self._detect_db_type()
        
    def _detect_db_type(self) -> str:
        """Detect database type from engine"""
        dialect = str(self.db_engine.dialect.name).lower()
        if 'mysql' in dialect:
            return 'mysql'
        elif 'postgresql' in dialect or 'postgres' in dialect:
            return 'postgresql'
        elif 'sqlite' in dialect:
            return 'sqlite'
        else:
            return 'unknown'
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive query analysis"""
        try:
            # Parse the query
            parsed = sqlparse.parse(query)[0]
            
            # Basic analysis
            analysis = {
                'query_type': self._get_query_type(parsed),
                'complexity_score': self._calculate_complexity(parsed),
                'table_count': self._count_tables(parsed),
                'join_count': self._count_joins(parsed),
                'subquery_count': self._count_subqueries(parsed),
                'function_usage': self._analyze_functions(parsed),
                'where_clause_analysis': self._analyze_where_clause(parsed),
                'order_by_analysis': self._analyze_order_by(parsed),
                'group_by_analysis': self._analyze_group_by(parsed),
                'potential_issues': self._identify_potential_issues(parsed),
                'optimization_opportunities': self._find_optimization_opportunities(parsed)
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f"Query analysis failed: {str(e)}"}
    
    def _get_query_type(self, parsed) -> str:
        """Determine the type of SQL query"""
        query_str = str(parsed).upper().strip()
        if query_str.startswith('SELECT'):
            return 'SELECT'
        elif query_str.startswith('INSERT'):
            return 'INSERT'
        elif query_str.startswith('UPDATE'):
            return 'UPDATE'
        elif query_str.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _calculate_complexity(self, parsed) -> int:
        """Calculate query complexity score (1-10)"""
        complexity = 1
        query_str = str(parsed).upper()
        
        # Add complexity for various elements
        complexity += query_str.count('JOIN') * 2
        complexity += query_str.count('SUBQUERY') * 3
        complexity += query_str.count('UNION') * 2
        complexity += query_str.count('CASE') * 1
        complexity += query_str.count('EXISTS') * 2
        complexity += query_str.count('HAVING') * 1
        
        return min(complexity, 10)
    
    def _count_tables(self, parsed) -> int:
        """Count number of tables referenced"""
        # Simplified table counting
        query_str = str(parsed).upper()
        from_matches = re.findall(r'FROM\s+(\w+)', query_str)
        join_matches = re.findall(r'JOIN\s+(\w+)', query_str)
        return len(set(from_matches + join_matches))
    
    def _count_joins(self, parsed) -> int:
        """Count number of joins"""
        query_str = str(parsed).upper()
        return len(re.findall(r'\b(INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|JOIN)\b', query_str))
    
    def _count_subqueries(self, parsed) -> int:
        """Count number of subqueries"""
        query_str = str(parsed)
        return query_str.count('(SELECT')
    
    def _analyze_functions(self, parsed) -> Dict[str, List[str]]:
        """Analyze function usage in query"""
        query_str = str(parsed).upper()
        
        # Common SQL functions
        aggregate_functions = re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT)\s*\(', query_str)
        date_functions = re.findall(r'\b(DATE|YEAR|MONTH|DAY|NOW|CURDATE|DATE_FORMAT)\s*\(', query_str)
        string_functions = re.findall(r'\b(CONCAT|SUBSTRING|UPPER|LOWER|TRIM)\s*\(', query_str)
        
        return {
            'aggregate': list(set(aggregate_functions)),
            'date': list(set(date_functions)),
            'string': list(set(string_functions))
        }
    
    def _analyze_where_clause(self, parsed) -> Dict[str, Any]:
        """Analyze WHERE clause for optimization opportunities"""
        query_str = str(parsed).upper()
        
        # Look for potential issues
        has_functions_in_where = bool(re.search(r'WHERE.*\b(YEAR|MONTH|DAY|UPPER|LOWER)\s*\(', query_str))
        has_like_patterns = bool(re.search(r'LIKE\s+[\'"]%.*%[\'"]', query_str))
        has_or_conditions = 'OR' in query_str
        has_not_conditions = ' NOT ' in query_str
        
        return {
            'has_functions_in_where': has_functions_in_where,
            'has_like_patterns': has_like_patterns,
            'has_or_conditions': has_or_conditions,
            'has_not_conditions': has_not_conditions
        }
    
    def _analyze_order_by(self, parsed) -> Dict[str, Any]:
        """Analyze ORDER BY clause"""
        query_str = str(parsed).upper()
        has_order_by = 'ORDER BY' in query_str
        has_functions_in_order = bool(re.search(r'ORDER BY.*\b(YEAR|MONTH|DAY|UPPER|LOWER)\s*\(', query_str))
        
        return {
            'has_order_by': has_order_by,
            'has_functions_in_order': has_functions_in_order
        }
    
    def _analyze_group_by(self, parsed) -> Dict[str, Any]:
        """Analyze GROUP BY clause"""
        query_str = str(parsed).upper()
        has_group_by = 'GROUP BY' in query_str
        has_having = 'HAVING' in query_str
        
        return {
            'has_group_by': has_group_by,
            'has_having': has_having
        }
    
    def _identify_potential_issues(self, parsed) -> List[str]:
        """Identify potential performance issues"""
        issues = []
        query_str = str(parsed).upper()
        
        # Check for common issues
        if 'SELECT *' in query_str:
            issues.append("Using SELECT * - consider specifying only needed columns")
        
        if re.search(r'WHERE.*\b(YEAR|MONTH|DAY)\s*\(', query_str):
            issues.append("Functions in WHERE clause may prevent index usage")
        
        if re.search(r'LIKE\s+[\'"]%.*%[\'"]', query_str):
            issues.append("Leading wildcard in LIKE pattern prevents index usage")
        
        if 'ORDER BY' in query_str and 'LIMIT' not in query_str:
            issues.append("ORDER BY without LIMIT may be inefficient for large datasets")
        
        if query_str.count('JOIN') > 5:
            issues.append("Many joins detected - consider query decomposition")
        
        return issues
    
    def _find_optimization_opportunities(self, parsed) -> List[str]:
        """Find optimization opportunities"""
        opportunities = []
        query_str = str(parsed).upper()
        
        if 'DISTINCT' in query_str:
            opportunities.append("Consider if DISTINCT is necessary or can be replaced with GROUP BY")
        
        if 'UNION' in query_str and 'UNION ALL' not in query_str:
            opportunities.append("Consider UNION ALL if duplicates are not a concern")
        
        if re.search(r'WHERE.*IN\s*\(SELECT', query_str):
            opportunities.append("Consider replacing IN subquery with EXISTS for better performance")
        
        if 'ORDER BY' in query_str:
            opportunities.append("Ensure appropriate indexes exist for ORDER BY columns")
        
        return opportunities


class IndexRecommendationEngine:
    """Generate intelligent index recommendations"""
    
    def __init__(self, db_engine, db_type: str):
        self.db_engine = db_engine
        self.db_type = db_type
    
    def recommend_indexes(self, query: str, table_schema: Dict) -> List[Dict[str, Any]]:
        """Generate index recommendations for a query"""
        recommendations = []
        
        try:
            # Parse query to extract table and column information
            parsed = sqlparse.parse(query)[0]
            query_analysis = self._analyze_query_for_indexes(parsed)
            
            # Generate recommendations based on analysis
            for table, columns in query_analysis.items():
                if table in table_schema:
                    table_recommendations = self._generate_table_index_recommendations(
                        table, columns, table_schema[table]
                    )
                    recommendations.extend(table_recommendations)
            
            return recommendations
            
        except Exception as e:
            return [{'error': f"Index recommendation failed: {str(e)}"}]
    
    def _analyze_query_for_indexes(self, parsed) -> Dict[str, Dict[str, List[str]]]:
        """Analyze query to identify columns that would benefit from indexes"""
        # This is a simplified implementation
        # In a real system, you'd use a proper SQL parser
        query_str = str(parsed)
        
        # Extract WHERE clause columns
        where_columns = self._extract_where_columns(query_str)
        
        # Extract JOIN columns
        join_columns = self._extract_join_columns(query_str)
        
        # Extract ORDER BY columns
        order_columns = self._extract_order_columns(query_str)
        
        # Combine all column usage information
        table_analysis = {}
        for table, columns in where_columns.items():
            if table not in table_analysis:
                table_analysis[table] = {'where': [], 'join': [], 'order': []}
            table_analysis[table]['where'] = columns
        
        for table, columns in join_columns.items():
            if table not in table_analysis:
                table_analysis[table] = {'where': [], 'join': [], 'order': []}
            table_analysis[table]['join'] = columns
        
        for table, columns in order_columns.items():
            if table not in table_analysis:
                table_analysis[table] = {'where': [], 'join': [], 'order': []}
            table_analysis[table]['order'] = columns
        
        return table_analysis
    
    def _extract_where_columns(self, query: str) -> Dict[str, List[str]]:
        """Extract columns used in WHERE clauses"""
        # Simplified extraction - in practice, use proper SQL parsing
        where_pattern = r'WHERE\s+.*?(?=GROUP BY|ORDER BY|HAVING|LIMIT|$)'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(0)
            # Extract table.column or column references
            column_pattern = r'(\w+)\.(\w+)|(\w+)\s*[=<>!]'
            matches = re.findall(column_pattern, where_clause)
            
            table_columns = {}
            for match in matches:
                if match[0] and match[1]:  # table.column format
                    table = match[0]
                    column = match[1]
                    if table not in table_columns:
                        table_columns[table] = []
                    table_columns[table].append(column)
            
            return table_columns
        
        return {}
    
    def _extract_join_columns(self, query: str) -> Dict[str, List[str]]:
        """Extract columns used in JOIN conditions"""
        join_pattern = r'JOIN\s+(\w+).*?ON\s+(.*?)(?=JOIN|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT|$)'
        matches = re.findall(join_pattern, query, re.IGNORECASE | re.DOTALL)
        
        table_columns = {}
        for table, condition in matches:
            # Extract columns from join condition
            column_pattern = r'(\w+)\.(\w+)'
            column_matches = re.findall(column_pattern, condition)
            
            for table_name, column in column_matches:
                if table_name not in table_columns:
                    table_columns[table_name] = []
                table_columns[table_name].append(column)
        
        return table_columns
    
    def _extract_order_columns(self, query: str) -> Dict[str, List[str]]:
        """Extract columns used in ORDER BY"""
        order_pattern = r'ORDER BY\s+(.*?)(?=LIMIT|$)'
        order_match = re.search(order_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if order_match:
            order_clause = order_match.group(1)
            column_pattern = r'(\w+)\.(\w+)|(\w+)'
            matches = re.findall(column_pattern, order_clause)
            
            table_columns = {}
            for match in matches:
                if match[0] and match[1]:  # table.column format
                    table = match[0]
                    column = match[1]
                    if table not in table_columns:
                        table_columns[table] = []
                    table_columns[table].append(column)
        
        return table_columns
    
    def _generate_table_index_recommendations(self, table: str, column_usage: Dict, table_info: Dict) -> List[Dict[str, Any]]:
        """Generate index recommendations for a specific table"""
        recommendations = []
        
        # Recommend indexes for WHERE clause columns
        for column in column_usage.get('where', []):
            recommendations.append({
                'type': 'single_column_index',
                'table': table,
                'columns': [column],
                'reason': f"Column {column} used in WHERE clause",
                'priority': 'HIGH',
                'sql': self._generate_index_sql(table, [column], 'where')
            })
        
        # Recommend indexes for JOIN columns
        for column in column_usage.get('join', []):
            recommendations.append({
                'type': 'single_column_index',
                'table': table,
                'columns': [column],
                'reason': f"Column {column} used in JOIN condition",
                'priority': 'HIGH',
                'sql': self._generate_index_sql(table, [column], 'join')
            })
        
        # Recommend composite indexes for WHERE + ORDER BY
        where_cols = column_usage.get('where', [])
        order_cols = column_usage.get('order', [])
        if where_cols and order_cols:
            composite_cols = where_cols + order_cols
            recommendations.append({
                'type': 'composite_index',
                'table': table,
                'columns': composite_cols,
                'reason': "Composite index for WHERE and ORDER BY optimization",
                'priority': 'MEDIUM',
                'sql': self._generate_index_sql(table, composite_cols, 'composite')
            })
        
        return recommendations
    
    def _generate_index_sql(self, table: str, columns: List[str], index_type: str) -> str:
        """Generate SQL for creating indexes"""
        index_name = f"idx_{table}_{'_'.join(columns)}"
        columns_str = ', '.join(columns)
        
        if self.db_type == 'mysql':
            return f"CREATE INDEX {index_name} ON {table} ({columns_str});"
        elif self.db_type == 'postgresql':
            return f"CREATE INDEX {index_name} ON {table} ({columns_str});"
        else:
            return f"CREATE INDEX {index_name} ON {table} ({columns_str});"


class QueryOptimizer:
    """Main query optimization engine"""
    
    def __init__(self, db_engine):
        self.db_engine = db_engine
        self.analyzer = QueryAnalyzer(db_engine)
        self.index_engine = IndexRecommendationEngine(db_engine, self.analyzer.db_type)
    
    def optimize_query(self, query: str, optimization_level: OptimizationLevel = OptimizationLevel.INTERMEDIATE) -> Dict[str, Any]:
        """Comprehensive query optimization"""
        
        # Analyze the query
        analysis = self.analyzer.analyze_query(query)
        
        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(query, analysis, optimization_level)
        
        # Get index recommendations
        # Note: This would need actual table schema information
        index_recommendations = []  # self.index_engine.recommend_indexes(query, table_schema)
        
        # Generate optimized query variants
        optimized_queries = self._generate_optimized_queries(query, analysis)
        
        return {
            'original_query': query,
            'analysis': analysis,
            'suggestions': suggestions,
            'index_recommendations': index_recommendations,
            'optimized_queries': optimized_queries,
            'optimization_level': optimization_level.value
        }
    
    def _generate_optimization_suggestions(self, query: str, analysis: Dict, level: OptimizationLevel) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []
        
        # Basic optimizations
        if 'SELECT *' in query.upper():
            suggestions.append(OptimizationSuggestion(
                type="column_selection",
                priority="HIGH",
                description="Replace SELECT * with specific column names to reduce data transfer",
                sql_example="SELECT col1, col2, col3 FROM table",
                expected_improvement="20-50% reduction in I/O",
                implementation_effort="LOW"
            ))
        
        # Add more suggestions based on analysis
        for issue in analysis.get('potential_issues', []):
            if "Functions in WHERE clause" in issue:
                suggestions.append(OptimizationSuggestion(
                    type="where_optimization",
                    priority="HIGH",
                    description="Avoid functions in WHERE clause to enable index usage",
                    sql_example="Use WHERE date_column >= '2023-01-01' instead of WHERE YEAR(date_column) = 2023",
                    expected_improvement="Significant performance improvement with proper indexes",
                    implementation_effort="MEDIUM"
                ))
        
        return suggestions
    
    def _generate_optimized_queries(self, query: str, analysis: Dict) -> List[Dict[str, str]]:
        """Generate optimized query variants"""
        optimized_queries = []
        
        # Example: Add LIMIT if missing and ORDER BY present
        if 'ORDER BY' in query.upper() and 'LIMIT' not in query.upper():
            limited_query = query.rstrip(';') + ' LIMIT 1000;'
            optimized_queries.append({
                'type': 'add_limit',
                'description': 'Added LIMIT to prevent large result sets',
                'query': limited_query
            })
        
        return optimized_queries
