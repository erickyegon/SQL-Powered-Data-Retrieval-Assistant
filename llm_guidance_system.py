"""
Enhanced LLM Guidance System
Provides intelligent query decomposition, context-aware prompting, and advanced SQL generation
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from utils import call_groq_llm
from advanced_prompts import PromptTemplateManager, QueryEnhancer


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class BusinessDomain(Enum):
    """Business domain types"""
    FINANCE = "finance"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    HR = "hr"
    GENERAL = "general"


@dataclass
class QueryContext:
    """Context information for query generation"""
    user_question: str
    business_domain: BusinessDomain
    complexity_level: QueryComplexity
    schema_info: Dict[str, Any]
    previous_queries: List[str]
    user_expertise: str  # beginner, intermediate, advanced
    performance_requirements: str  # fast, balanced, comprehensive


@dataclass
class QueryDecomposition:
    """Decomposed query components"""
    main_objective: str
    sub_questions: List[str]
    required_tables: List[str]
    required_joins: List[str]
    filters_needed: List[str]
    aggregations_needed: List[str]
    complexity_score: int


class QueryDecomposer:
    """Decompose complex queries into manageable components"""
    
    def __init__(self):
        self.prompt_manager = PromptTemplateManager()
    
    def decompose_query(self, user_question: str, schema_info: Dict) -> QueryDecomposition:
        """Decompose a complex user question into components"""
        
        # Analyze the question
        analysis = self._analyze_question(user_question)
        
        # Identify required components
        components = self._identify_components(user_question, schema_info, analysis)
        
        return QueryDecomposition(
            main_objective=analysis['main_objective'],
            sub_questions=components['sub_questions'],
            required_tables=components['tables'],
            required_joins=components['joins'],
            filters_needed=components['filters'],
            aggregations_needed=components['aggregations'],
            complexity_score=analysis['complexity_score']
        )
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the user question to understand intent"""
        
        # Keywords that indicate different types of analysis
        time_keywords = ['trend', 'over time', 'monthly', 'yearly', 'quarterly', 'growth', 'change']
        comparison_keywords = ['compare', 'versus', 'vs', 'difference', 'better', 'worse']
        ranking_keywords = ['top', 'bottom', 'best', 'worst', 'highest', 'lowest', 'rank']
        aggregation_keywords = ['total', 'sum', 'average', 'count', 'maximum', 'minimum']
        
        question_lower = question.lower()
        
        # Determine main objective
        main_objective = "data_retrieval"  # default
        
        if any(keyword in question_lower for keyword in time_keywords):
            main_objective = "time_series_analysis"
        elif any(keyword in question_lower for keyword in comparison_keywords):
            main_objective = "comparative_analysis"
        elif any(keyword in question_lower for keyword in ranking_keywords):
            main_objective = "ranking_analysis"
        elif any(keyword in question_lower for keyword in aggregation_keywords):
            main_objective = "aggregation_analysis"
        
        # Calculate complexity score
        complexity_score = 1
        complexity_score += len(re.findall(r'\band\b|\bor\b', question_lower))  # Multiple conditions
        complexity_score += len(re.findall(r'\bby\b', question_lower))  # Grouping
        complexity_score += len(re.findall(r'\bwhere\b|\bwhen\b|\bif\b', question_lower))  # Filtering
        
        return {
            'main_objective': main_objective,
            'complexity_score': min(complexity_score, 10),
            'has_time_component': any(keyword in question_lower for keyword in time_keywords),
            'has_comparison': any(keyword in question_lower for keyword in comparison_keywords),
            'has_ranking': any(keyword in question_lower for keyword in ranking_keywords),
            'has_aggregation': any(keyword in question_lower for keyword in aggregation_keywords)
        }
    
    def _identify_components(self, question: str, schema_info: Dict, analysis: Dict) -> Dict[str, List[str]]:
        """Identify required database components"""
        
        # Extract potential table names from question
        tables = self._extract_table_references(question, schema_info)
        
        # Determine required joins
        joins = self._determine_joins(tables, schema_info)
        
        # Identify filters
        filters = self._extract_filters(question)
        
        # Identify aggregations
        aggregations = self._extract_aggregations(question, analysis)
        
        # Generate sub-questions for complex queries
        sub_questions = self._generate_sub_questions(question, analysis)
        
        return {
            'tables': tables,
            'joins': joins,
            'filters': filters,
            'aggregations': aggregations,
            'sub_questions': sub_questions
        }
    
    def _extract_table_references(self, question: str, schema_info: Dict) -> List[str]:
        """Extract potential table references from question"""
        tables = []
        question_lower = question.lower()
        
        # Look for business terms that might map to tables
        business_terms = {
            'customer': ['customers', 'customer', 'client'],
            'product': ['products', 'product', 'item'],
            'order': ['orders', 'order', 'purchase'],
            'sale': ['sales', 'sale', 'transaction'],
            'employee': ['employees', 'employee', 'staff'],
            'revenue': ['revenue', 'income', 'earnings'],
            'expense': ['expenses', 'expense', 'cost']
        }
        
        for table_category, terms in business_terms.items():
            if any(term in question_lower for term in terms):
                # Look for actual table names in schema that match
                for table_name in schema_info.get('tables', []):
                    if any(term in table_name.lower() for term in terms):
                        tables.append(table_name)
        
        return list(set(tables))
    
    def _determine_joins(self, tables: List[str], schema_info: Dict) -> List[str]:
        """Determine required joins between tables"""
        joins = []
        
        if len(tables) > 1:
            # This is simplified - in practice, you'd analyze foreign key relationships
            for i in range(len(tables) - 1):
                joins.append(f"JOIN {tables[i+1]} ON {tables[i]}.id = {tables[i+1]}.{tables[i]}_id")
        
        return joins
    
    def _extract_filters(self, question: str) -> List[str]:
        """Extract filter conditions from question"""
        filters = []
        question_lower = question.lower()
        
        # Date filters
        date_patterns = [
            r'in (\d{4})',  # year
            r'last (\d+) (month|year|day)',
            r'this (month|year|quarter)',
            r'between .* and .*'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, question_lower)
            if matches:
                filters.extend([f"Date filter: {match}" for match in matches])
        
        # Value filters
        if 'greater than' in question_lower or '>' in question:
            filters.append("Value filter: greater than")
        if 'less than' in question_lower or '<' in question:
            filters.append("Value filter: less than")
        
        return filters
    
    def _extract_aggregations(self, question: str, analysis: Dict) -> List[str]:
        """Extract aggregation requirements"""
        aggregations = []
        question_lower = question.lower()
        
        agg_patterns = {
            'sum': ['total', 'sum'],
            'avg': ['average', 'mean'],
            'count': ['count', 'number of', 'how many'],
            'max': ['maximum', 'highest', 'max'],
            'min': ['minimum', 'lowest', 'min']
        }
        
        for agg_type, keywords in agg_patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                aggregations.append(agg_type.upper())
        
        return list(set(aggregations))
    
    def _generate_sub_questions(self, question: str, analysis: Dict) -> List[str]:
        """Generate sub-questions for complex queries"""
        sub_questions = []
        
        if analysis['complexity_score'] > 5:
            # For complex queries, break down into steps
            if analysis['has_time_component']:
                sub_questions.append("What is the time range for analysis?")
            
            if analysis['has_comparison']:
                sub_questions.append("What entities are being compared?")
            
            if analysis['has_ranking']:
                sub_questions.append("What criteria should be used for ranking?")
            
            if analysis['has_aggregation']:
                sub_questions.append("What level of aggregation is needed?")
        
        return sub_questions


class ContextAwarePromptGenerator:
    """Generate context-aware prompts for better SQL generation"""
    
    def __init__(self):
        self.prompt_manager = PromptTemplateManager()
        self.query_enhancer = QueryEnhancer()
    
    def generate_enhanced_prompt(self, context: QueryContext) -> str:
        """Generate enhanced prompt based on context"""
        
        # Select appropriate template based on domain and complexity
        template_name = self._select_template(context)
        
        # Enhance the user question
        enhanced_question = self.query_enhancer.enhance_natural_language_query(
            context.user_question, str(context.schema_info)
        )
        
        # Add domain-specific context
        domain_context = self._get_domain_context(context.business_domain)
        
        # Add performance hints
        performance_hints = self._get_performance_hints(context.performance_requirements)
        
        # Generate the prompt
        base_prompt = self.prompt_manager.get_template(
            template_name,
            db_type="MySQL",  # This should be dynamic
            schema=str(context.schema_info),
            question=enhanced_question
        )
        
        # Add context enhancements
        enhanced_prompt = f"{base_prompt}\n\n"
        enhanced_prompt += f"## BUSINESS DOMAIN CONTEXT:\n{domain_context}\n\n"
        enhanced_prompt += f"## PERFORMANCE REQUIREMENTS:\n{performance_hints}\n\n"
        enhanced_prompt += f"## USER EXPERTISE LEVEL:\n{context.user_expertise}\n\n"
        
        if context.previous_queries:
            enhanced_prompt += f"## PREVIOUS QUERIES CONTEXT:\n"
            for i, query in enumerate(context.previous_queries[-3:], 1):  # Last 3 queries
                enhanced_prompt += f"{i}. {query}\n"
            enhanced_prompt += "\n"
        
        return enhanced_prompt
    
    def _select_template(self, context: QueryContext) -> str:
        """Select appropriate template based on context"""
        
        if context.business_domain == BusinessDomain.FINANCE:
            return "business_analyst"
        elif context.complexity_level == QueryComplexity.EXPERT:
            return "data_scientist"
        elif context.performance_requirements == "fast":
            return "performance_optimizer"
        else:
            return "business_analyst"  # Default
    
    def _get_domain_context(self, domain: BusinessDomain) -> str:
        """Get domain-specific context"""
        
        domain_contexts = {
            BusinessDomain.FINANCE: """
            Focus on financial metrics, KPIs, and regulatory compliance.
            Common patterns: revenue analysis, cost analysis, profitability, budget variance.
            Key considerations: accuracy, auditability, period comparisons.
            """,
            BusinessDomain.SALES: """
            Focus on sales performance, pipeline analysis, and customer metrics.
            Common patterns: conversion rates, sales trends, territory analysis.
            Key considerations: time-based analysis, segmentation, forecasting.
            """,
            BusinessDomain.MARKETING: """
            Focus on campaign performance, customer acquisition, and ROI analysis.
            Common patterns: funnel analysis, attribution, customer journey.
            Key considerations: multi-touch attribution, cohort analysis.
            """,
            BusinessDomain.OPERATIONS: """
            Focus on operational efficiency, process optimization, and resource utilization.
            Common patterns: throughput analysis, quality metrics, capacity planning.
            Key considerations: real-time monitoring, trend analysis.
            """,
            BusinessDomain.HR: """
            Focus on workforce analytics, performance management, and compliance.
            Common patterns: headcount analysis, retention rates, performance metrics.
            Key considerations: privacy compliance, demographic analysis.
            """,
            BusinessDomain.GENERAL: """
            General business analysis with focus on data accuracy and insights.
            Common patterns: descriptive statistics, trend analysis, comparisons.
            Key considerations: data quality, business relevance.
            """
        }
        
        return domain_contexts.get(domain, domain_contexts[BusinessDomain.GENERAL])
    
    def _get_performance_hints(self, requirements: str) -> str:
        """Get performance-specific hints"""
        
        performance_hints = {
            "fast": """
            Prioritize query execution speed:
            - Use appropriate LIMIT clauses
            - Minimize complex joins
            - Use indexes effectively
            - Consider approximate results for large datasets
            """,
            "balanced": """
            Balance between speed and comprehensiveness:
            - Optimize for common use cases
            - Use efficient aggregations
            - Consider query complexity vs. value
            """,
            "comprehensive": """
            Focus on complete and accurate results:
            - Include all relevant data
            - Use complex analytics when beneficial
            - Prioritize accuracy over speed
            - Include data quality checks
            """
        }
        
        return performance_hints.get(requirements, performance_hints["balanced"])


class LLMGuidanceSystem:
    """Main LLM guidance system"""
    
    def __init__(self):
        self.decomposer = QueryDecomposer()
        self.prompt_generator = ContextAwarePromptGenerator()
    
    def generate_guided_query(self, context: QueryContext) -> Dict[str, Any]:
        """Generate SQL query with intelligent guidance"""
        
        # Decompose the query if complex
        decomposition = self.decomposer.decompose_query(
            context.user_question, context.schema_info
        )
        
        # Generate enhanced prompt
        enhanced_prompt = self.prompt_generator.generate_enhanced_prompt(context)
        
        # Generate SQL query
        sql_query = call_groq_llm(enhanced_prompt)
        
        # Validate and enhance the query
        validation_result = self._validate_query(sql_query, context)
        
        return {
            'sql_query': sql_query,
            'decomposition': decomposition,
            'enhanced_prompt': enhanced_prompt,
            'validation': validation_result,
            'suggestions': self._generate_suggestions(decomposition, context)
        }
    
    def _validate_query(self, sql_query: str, context: QueryContext) -> Dict[str, Any]:
        """Validate the generated SQL query"""
        
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': []
        }
        
        if not sql_query or sql_query.strip() == "":
            validation['is_valid'] = False
            validation['issues'].append("No SQL query generated")
            return validation
        
        # Basic syntax checks
        if not sql_query.strip().upper().startswith('SELECT'):
            validation['warnings'].append("Query doesn't start with SELECT")
        
        # Performance checks
        if 'SELECT *' in sql_query.upper():
            validation['warnings'].append("Using SELECT * - consider specifying columns")
        
        if 'ORDER BY' in sql_query.upper() and 'LIMIT' not in sql_query.upper():
            validation['warnings'].append("ORDER BY without LIMIT may be slow")
        
        return validation
    
    def _generate_suggestions(self, decomposition: QueryDecomposition, context: QueryContext) -> List[str]:
        """Generate suggestions for query improvement"""
        
        suggestions = []
        
        if decomposition.complexity_score > 7:
            suggestions.append("Consider breaking this into multiple simpler queries")
        
        if len(decomposition.required_tables) > 5:
            suggestions.append("Many tables involved - ensure proper indexing")
        
        if context.user_expertise == "beginner":
            suggestions.append("Review the generated query to understand the logic")
        
        return suggestions


# Factory function
def create_llm_guidance_system() -> LLMGuidanceSystem:
    """Create LLM guidance system instance"""
    return LLMGuidanceSystem()
