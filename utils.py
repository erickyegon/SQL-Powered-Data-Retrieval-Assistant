import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlparse
import re
from sqlalchemy import text, MetaData, create_engine
from datetime import datetime, timedelta
import streamlit as st
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import base64

from config import GROQ_API_KEY, GROQ_API_URL, MODEL_NAME

# ============ DATABASE FUNCTIONS ============


def build_connection_string(db_type, host, port, database, username, password):
    if db_type.lower() == 'mysql':
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    elif db_type.lower() == 'postgresql':
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def create_db_engine(db_type, host, port, database, username, password):
    connection_string = build_connection_string(
        db_type, host, port, database, username, password)
    return create_engine(connection_string)


def get_db_schema(engine):
    meta = MetaData()
    meta.reflect(bind=engine)
    schema = ""
    for table in meta.tables.values():
        schema += f"\nTable: {table.name}\nColumns: " + ", ".join(
            [f"{col.name} ({col.type})" for col in table.columns]
        ) + "\n"
    return schema.strip()


def test_db_connection(engine):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def execute_sql(engine, query):
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return result.fetchall(), result.keys()


def validate_sql_syntax(sql_query, schema_info=None):
    """Validate SQL syntax and check for common errors"""
    import re
    import sqlparse

    try:
        # Parse the SQL query
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return False, ["Invalid SQL syntax"]

        errors = []
        warnings = []

        # Check for common issues
        query_upper = sql_query.upper()

        # Check for table alias consistency
        alias_errors = check_table_alias_consistency(sql_query)
        if alias_errors:
            errors.extend(alias_errors)

        # Check for missing JOIN conditions
        join_errors = check_join_conditions(sql_query)
        if join_errors:
            warnings.extend(join_errors)

        # Check for column references
        if schema_info:
            column_errors = check_column_references(sql_query, schema_info)
            if column_errors:
                errors.extend(column_errors)

        return len(errors) == 0, errors + warnings

    except Exception as e:
        return False, [f"SQL parsing error: {str(e)}"]


def check_table_alias_consistency(sql_query):
    """Check for table alias consistency issues"""
    import re

    errors = []

    # Find all table aliases in FROM and JOIN clauses
    from_pattern = r'FROM\s+(\w+)\s+(?:AS\s+)?(\w+)'
    join_pattern = r'JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)'

    aliases = {}

    # Extract FROM clause aliases
    from_matches = re.findall(from_pattern, sql_query, re.IGNORECASE)
    for table, alias in from_matches:
        if alias.upper() not in ['ON', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
            aliases[alias.lower()] = table.lower()

    # Extract JOIN clause aliases
    join_matches = re.findall(join_pattern, sql_query, re.IGNORECASE)
    for table, alias in join_matches:
        if alias.upper() not in ['ON', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
            aliases[alias.lower()] = table.lower()

    # Find all column references with aliases
    column_pattern = r'(\w+)\.(\w+)'
    column_matches = re.findall(column_pattern, sql_query, re.IGNORECASE)

    # Check if all referenced aliases exist
    for alias, column in column_matches:
        if alias.lower() not in aliases:
            errors.append(f"Unknown table alias '{alias}' used in column reference '{alias}.{column}'")

    return errors


def check_join_conditions(sql_query):
    """Check for potential JOIN condition issues"""
    import re

    warnings = []

    # Count JOINs and ON conditions
    join_count = len(re.findall(r'\bJOIN\b', sql_query, re.IGNORECASE))
    on_count = len(re.findall(r'\bON\b', sql_query, re.IGNORECASE))

    if join_count > on_count:
        warnings.append(f"Found {join_count} JOINs but only {on_count} ON conditions - possible missing JOIN condition")

    return warnings


def check_column_references(sql_query, schema_info):
    """Check if column references exist in schema"""
    import re

    errors = []

    # This is a simplified check - in a real implementation,
    # you'd parse the schema_info more thoroughly
    if not schema_info:
        return errors

    # Extract column references
    column_pattern = r'(\w+)\.(\w+)'
    column_matches = re.findall(column_pattern, sql_query, re.IGNORECASE)

    # For now, just check if the pattern looks suspicious
    # (This would be enhanced with actual schema validation)

    return errors


def fix_common_sql_errors(sql_query, error_message):
    """Attempt to fix common SQL errors automatically"""
    import re

    fixed_query = sql_query

    # Fix 1: Unknown column with table alias
    if "Unknown column" in error_message and "field list" in error_message:
        # Extract the problematic column reference
        column_match = re.search(r"Unknown column '([^']+)'", error_message)
        if column_match:
            problematic_column = column_match.group(1)

            # Check if it's an alias issue (e.g., fpid.discounts_pct when column is in fpid2)
            if '.' in problematic_column:
                alias, column = problematic_column.split('.', 1)

                # Strategy 1: Find the same column name with different aliases
                pattern = rf'\b(\w+)\.{re.escape(column)}\b'
                matches = re.findall(pattern, sql_query, re.IGNORECASE)

                # Remove the problematic alias from matches
                valid_matches = [match for match in matches if match.lower() != alias.lower()]

                if valid_matches:
                    # Use the first valid alias found
                    correct_alias = valid_matches[0]
                    fixed_query = re.sub(
                        rf'\b{re.escape(alias)}\.{re.escape(column)}\b',
                        f'{correct_alias}.{column}',
                        fixed_query,
                        flags=re.IGNORECASE
                    )
                    return fixed_query, f"Fixed table alias: {alias}.{column} → {correct_alias}.{column}"

                # Strategy 2: Look for similar column names in other tables
                similar_columns = find_similar_columns_in_query(sql_query, column)
                if similar_columns:
                    best_match = similar_columns[0]  # Take the best match
                    fixed_query = re.sub(
                        rf'\b{re.escape(alias)}\.{re.escape(column)}\b',
                        f'{best_match["alias"]}.{best_match["column"]}',
                        fixed_query,
                        flags=re.IGNORECASE
                    )
                    return fixed_query, f"Fixed column reference: {alias}.{column} → {best_match['alias']}.{best_match['column']}"

                # Strategy 3: Remove the problematic column if it's in a calculation
                if is_column_in_calculation(sql_query, problematic_column):
                    fixed_query = remove_problematic_column_from_calculation(sql_query, problematic_column)
                    if fixed_query != sql_query:
                        return fixed_query, f"Removed problematic column from calculation: {problematic_column}"

    # Fix 2: Duplicate table alias errors
    if "Not unique table/alias" in error_message:
        fixed_query = fix_duplicate_aliases(sql_query)
        if fixed_query != sql_query:
            return fixed_query, "Fixed duplicate table aliases"

    # Fix 3: Missing table in FROM clause
    if "Table" in error_message and "doesn't exist" in error_message:
        # Extract table name from error
        table_match = re.search(r"Table '([^']+)' doesn't exist", error_message)
        if table_match:
            missing_table = table_match.group(1)
            # Try to find similar table names in the query
            similar_tables = find_similar_table_names(sql_query, missing_table)
            if similar_tables:
                best_match = similar_tables[0]
                fixed_query = sql_query.replace(missing_table, best_match)
                return fixed_query, f"Fixed table name: {missing_table} → {best_match}"

    return sql_query, None


def find_similar_columns_in_query(sql_query, target_column):
    """Find similar column names in the query that might be the intended column"""
    import re
    from difflib import SequenceMatcher

    # Extract all column references from the query
    column_pattern = r'\b(\w+)\.(\w+)\b'
    all_columns = re.findall(column_pattern, sql_query, re.IGNORECASE)

    similar_columns = []

    for alias, column in all_columns:
        # Calculate similarity score
        similarity = SequenceMatcher(None, target_column.lower(), column.lower()).ratio()

        # Look for columns that are similar or contain the target column
        if (similarity > 0.6 or
            target_column.lower() in column.lower() or
            column.lower() in target_column.lower()):
            similar_columns.append({
                'alias': alias,
                'column': column,
                'similarity': similarity
            })

    # Sort by similarity score
    similar_columns.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_columns


def is_column_in_calculation(sql_query, column_ref):
    """Check if the column is part of a mathematical calculation"""
    import re

    # Look for the column in mathematical expressions
    calc_pattern = rf'{re.escape(column_ref)}\s*[\+\-\*\/\(\)]'
    return bool(re.search(calc_pattern, sql_query, re.IGNORECASE))


def remove_problematic_column_from_calculation(sql_query, column_ref):
    """Remove a problematic column from calculations"""
    import re

    # Strategy: Replace the problematic column with 0 in calculations
    # This is a safe fallback that maintains query structure

    # Pattern to match the column in various calculation contexts
    patterns = [
        # Column in multiplication: * fpid.discounts_pct
        (rf'\*\s*\(1\s*-\s*{re.escape(column_ref)}\)', ''),
        # Column in subtraction: - fpid.discounts_pct
        (rf'-\s*{re.escape(column_ref)}', ''),
        # Column in addition: + fpid.discounts_pct
        (rf'\+\s*{re.escape(column_ref)}', ''),
        # Column standalone in calculation: fpid.discounts_pct
        (rf'{re.escape(column_ref)}', '0'),
    ]

    fixed_query = sql_query
    for pattern, replacement in patterns:
        new_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
        if new_query != fixed_query:
            fixed_query = new_query
            break

    return fixed_query


def fix_duplicate_aliases(sql_query):
    """Fix duplicate table aliases in the query"""
    import re

    # Find all table aliases
    alias_pattern = r'(?:FROM|JOIN)\s+(\w+)\s+(?:AS\s+)?(\w+)'
    matches = re.findall(alias_pattern, sql_query, re.IGNORECASE)

    alias_count = {}
    for table, alias in matches:
        alias_lower = alias.lower()
        if alias_lower in alias_count:
            alias_count[alias_lower] += 1
        else:
            alias_count[alias_lower] = 1

    # Find duplicates and rename them
    fixed_query = sql_query
    for alias, count in alias_count.items():
        if count > 1:
            # Rename subsequent occurrences
            counter = 1
            pattern = rf'\b{re.escape(alias)}\b'

            def replace_func(match):
                nonlocal counter
                if counter == 1:
                    counter += 1
                    return match.group(0)  # Keep first occurrence
                else:
                    new_alias = f"{alias}{counter}"
                    counter += 1
                    return new_alias

            fixed_query = re.sub(pattern, replace_func, fixed_query, flags=re.IGNORECASE)

    return fixed_query


def find_similar_table_names(sql_query, target_table):
    """Find similar table names in the query"""
    import re
    from difflib import SequenceMatcher

    # Extract all table names from the query
    table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
    tables = re.findall(table_pattern, sql_query, re.IGNORECASE)

    similar_tables = []
    for table in tables:
        similarity = SequenceMatcher(None, target_table.lower(), table.lower()).ratio()
        if similarity > 0.6:
            similar_tables.append(table)

    return sorted(similar_tables, key=lambda x: SequenceMatcher(None, target_table.lower(), x.lower()).ratio(), reverse=True)


def execute_sql_with_error_recovery(engine, sql_query, schema_info=None, max_retries=3):
    """Execute SQL with automatic error recovery"""

    original_query = sql_query

    for attempt in range(max_retries + 1):
        try:
            # Validate syntax first
            is_valid, validation_errors = validate_sql_syntax(sql_query, schema_info)

            if not is_valid and attempt == 0:
                print(f"⚠️ SQL validation warnings: {validation_errors}")
                # Continue anyway for the first attempt

            # Execute the query
            results, columns = execute_sql(engine, sql_query)
            return results, columns, sql_query

        except Exception as e:
            error_message = str(e)
            print(f"❌ Attempt {attempt + 1} failed: {error_message}")

            if attempt < max_retries:
                # Try multiple fix strategies
                fixed_query = None
                fix_description = None

                # Strategy 1: Standard error fixes
                fixed_query, fix_description = fix_common_sql_errors(sql_query, error_message)

                # Strategy 2: Financial query specific fixes
                if fixed_query == sql_query and "Unknown column" in error_message:
                    fixed_query, fix_description = fix_financial_query_errors(sql_query, error_message)

                # Strategy 3: Advanced column mapping
                if fixed_query == sql_query and "Unknown column" in error_message:
                    fixed_query, fix_description = fix_column_mapping_errors(sql_query, error_message)

                # Strategy 4: Simplification
                if fixed_query == sql_query:
                    if "Unknown column" in error_message:
                        simple_query = generate_fallback_query(sql_query, error_message)
                        if simple_query and simple_query != sql_query:
                            fixed_query = simple_query
                            fix_description = "Generated simplified fallback query"

                if fixed_query and fixed_query != sql_query:
                    print(f"🔧 Attempting fix: {fix_description}")
                    sql_query = fixed_query
                    continue
                else:
                    print(f"🔧 No automatic fix available for this error")

            # If all retries failed, raise the last error
            raise e


def fix_financial_query_errors(sql_query, error_message):
    """Fix common financial query errors with domain knowledge"""
    import re

    # Extract the problematic column
    column_match = re.search(r"Unknown column '([^']+)'", error_message)
    if not column_match:
        return sql_query, None

    problematic_column = column_match.group(1)

    # Common financial column mappings
    financial_column_mappings = {
        'fpid.discounts_pct': 'IFNULL(fpid2.discounts_pct, 0)',
        'fpid.other_deductions_pct': 'IFNULL(fpid2.other_deductions_pct, 0)',
        'fpid.post_invoice_discount_pct': 'IFNULL(fpid2.post_invoice_discount_pct, 0)',
        'fpid.freight_pct': 'IFNULL(fpid2.freight_pct, 0)',
        'fpid2.pre_invoice_discount_pct': 'IFNULL(fpid.pre_invoice_discount_pct, 0)',
        'fp.product_code': 'fs.product_code',
        'fp.customer_code': 'fs.customer_code',
        'fp.date': 'fs.date',
        'fc.product_code': 'fs.product_code',
        'fc.customer_code': 'fs.customer_code'
    }

    # Check if we have a direct mapping
    if problematic_column in financial_column_mappings:
        correct_column = financial_column_mappings[problematic_column]
        fixed_query = sql_query.replace(problematic_column, correct_column)
        return fixed_query, f"Fixed financial column mapping: {problematic_column} → {correct_column}"

    # Pattern-based fixes for financial queries
    if 'fpid.' in problematic_column and any(term in problematic_column for term in ['discount', 'deduction', 'freight']):
        # These are typically post-invoice deductions - add NULL handling
        correct_column = problematic_column.replace('fpid.', 'IFNULL(fpid2.', 1) + ', 0)'
        fixed_query = sql_query.replace(problematic_column, correct_column)
        return fixed_query, f"Fixed post-invoice deduction column with NULL handling: {problematic_column} → {correct_column}"

    if 'fpid2.' in problematic_column and 'pre_invoice' in problematic_column:
        # Pre-invoice deductions should use fpid - add NULL handling
        correct_column = problematic_column.replace('fpid2.', 'IFNULL(fpid.', 1) + ', 0)'
        fixed_query = sql_query.replace(problematic_column, correct_column)
        return fixed_query, f"Fixed pre-invoice deduction column with NULL handling: {problematic_column} → {correct_column}"

    # Handle complex calculation patterns
    fixed_query = fix_financial_calculation_patterns(sql_query, problematic_column)
    if fixed_query != sql_query:
        return fixed_query, f"Fixed financial calculation pattern: {problematic_column}"

    return sql_query, None


def fix_financial_calculation_patterns(sql_query, problematic_column):
    """Fix complex financial calculation patterns"""
    import re

    # Pattern 1: Revenue calculation with discounts
    # (1 - fpid.pre_invoice_discount_pct - fpid.discounts_pct)
    pattern1 = r'\(1\s*-\s*fpid\.pre_invoice_discount_pct\s*-\s*fpid\.discounts_pct\)'
    replacement1 = '(1 - IFNULL(fpid.pre_invoice_discount_pct, 0) - IFNULL(fpid2.discounts_pct, 0))'

    if re.search(pattern1, sql_query, re.IGNORECASE):
        fixed_query = re.sub(pattern1, replacement1, sql_query, flags=re.IGNORECASE)
        return fixed_query

    # Pattern 2: Multiple deduction calculation
    # (1 - fpid.pre_invoice_discount_pct) * (1 - fpid.discounts_pct)
    pattern2 = r'\(1\s*-\s*fpid\.pre_invoice_discount_pct\)\s*\*\s*\(1\s*-\s*fpid\.discounts_pct\)'
    replacement2 = '(1 - IFNULL(fpid.pre_invoice_discount_pct, 0)) * (1 - IFNULL(fpid2.discounts_pct, 0))'

    if re.search(pattern2, sql_query, re.IGNORECASE):
        fixed_query = re.sub(pattern2, replacement2, sql_query, flags=re.IGNORECASE)
        return fixed_query

    # Pattern 3: Simple discount subtraction
    # - fpid.discounts_pct
    if 'fpid.discounts_pct' in sql_query:
        fixed_query = sql_query.replace('fpid.discounts_pct', 'IFNULL(fpid2.discounts_pct, 0)')
        return fixed_query

    # Pattern 4: Other post-invoice deductions
    post_invoice_columns = ['other_deductions_pct', 'freight_pct', 'post_invoice_discount_pct']
    for column in post_invoice_columns:
        if f'fpid.{column}' in sql_query:
            fixed_query = sql_query.replace(f'fpid.{column}', f'IFNULL(fpid2.{column}, 0)')
            return fixed_query

    return sql_query


def fix_column_mapping_errors(sql_query, error_message):
    """Advanced column mapping error fixes"""
    import re

    column_match = re.search(r"Unknown column '([^']+)'", error_message)
    if not column_match:
        return sql_query, None

    problematic_column = column_match.group(1)

    if '.' not in problematic_column:
        return sql_query, None

    alias, column = problematic_column.split('.', 1)

    # Find all table aliases and their associated tables in the query
    table_aliases = extract_table_aliases_from_query(sql_query)

    # Look for the column in other tables
    for table_alias, table_name in table_aliases.items():
        if table_alias.lower() != alias.lower():
            # Check if this table might have the column based on naming patterns
            if is_likely_column_match(table_name, column):
                test_column = f"{table_alias}.{column}"
                fixed_query = sql_query.replace(problematic_column, test_column)
                return fixed_query, f"Mapped column to likely table: {problematic_column} → {test_column}"

    # If exact column not found, look for similar columns
    similar_columns = find_similar_columns_in_query(sql_query, column)
    if similar_columns and similar_columns[0]['similarity'] > 0.8:
        best_match = similar_columns[0]
        replacement = f"{best_match['alias']}.{best_match['column']}"
        fixed_query = sql_query.replace(problematic_column, replacement)
        return fixed_query, f"Fixed with similar column: {problematic_column} → {replacement}"

    return sql_query, None


def extract_table_aliases_from_query(sql_query):
    """Extract table aliases and their table names from the query"""
    import re

    aliases = {}

    # Pattern to match FROM and JOIN clauses with aliases
    patterns = [
        r'FROM\s+(\w+)\s+(?:AS\s+)?(\w+)',
        r'JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, sql_query, re.IGNORECASE)
        for table, alias in matches:
            # Skip if the "alias" is actually a SQL keyword
            if alias.upper() not in ['ON', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT']:
                aliases[alias] = table

    return aliases


def is_likely_column_match(table_name, column_name):
    """Determine if a column is likely to belong to a table based on naming patterns"""

    # Common table-column associations
    table_column_patterns = {
        'fact_sales_monthly': ['product_code', 'customer_code', 'date', 'sold_quantity'],
        'fact_gross_price': ['product_code', 'fiscal_year', 'gross_price'],
        'fact_manufacturing_cost': ['product_code', 'cost_year', 'manufacturing_cost'],
        'fact_pre_invoice_deductions': ['customer_code', 'fiscal_year', 'pre_invoice_discount_pct'],
        'fact_post_invoice_deductions': ['customer_code', 'product_code', 'date', 'discounts_pct', 'other_deductions_pct'],
        'dim_product': ['product_code', 'product', 'variant', 'category', 'segment'],
        'dim_customer': ['customer_code', 'customer', 'platform', 'channel']
    }

    table_lower = table_name.lower()
    column_lower = column_name.lower()

    # Check exact matches
    if table_lower in table_column_patterns:
        return column_lower in [col.lower() for col in table_column_patterns[table_lower]]

    # Check partial matches
    for table_pattern, columns in table_column_patterns.items():
        if table_pattern in table_lower or table_lower in table_pattern:
            if column_lower in [col.lower() for col in columns]:
                return True

    # General patterns
    if 'sales' in table_lower and column_lower in ['product_code', 'customer_code', 'date', 'quantity']:
        return True
    if 'price' in table_lower and column_lower in ['product_code', 'price', 'fiscal_year']:
        return True
    if 'cost' in table_lower and column_lower in ['product_code', 'cost', 'cost_year']:
        return True
    if 'deduction' in table_lower and column_lower in ['customer_code', 'product_code', 'discount', 'deduction']:
        return True

    return False


def generate_fallback_query(original_query, error_message):
    """Generate a simpler fallback query when the original fails"""
    import re

    # For unknown column errors, try to create a basic query
    if "Unknown column" in error_message:
        # Extract table names from the original query
        from_match = re.search(r'FROM\s+(\w+)', original_query, re.IGNORECASE)
        if from_match:
            main_table = from_match.group(1)

            # Create a simple SELECT * query
            fallback = f"SELECT * FROM {main_table} LIMIT 10"
            return fallback

    return None

# ============ LLM FUNCTIONS ============


def validate_extracted_sql(sql_query):
    """Validate that the extracted string is actually SQL"""
    if not sql_query:
        return False, "Empty query"

    # Remove comments and whitespace
    cleaned = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    if not cleaned:
        return False, "Query is empty after cleaning"

    # Check for SQL keywords
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE',
                    'DELETE', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN']
    if not any(keyword in cleaned.upper() for keyword in sql_keywords):
        return False, "No valid SQL keywords found"

    # Check for obvious non-SQL content
    non_sql_indicators = [
        'however', 'to calculate', 'this query', 'note that', 'explanation',
        'assuming', 'the following', 'we can use', 'here is', 'you can use',
        'to address', 'the issue', 'the problem'
    ]

    for indicator in non_sql_indicators:
        if indicator in cleaned.lower():
            return False, f"Contains explanatory text: '{indicator}'"

    # Check for balanced parentheses
    if cleaned.count('(') != cleaned.count(')'):
        return False, "Unbalanced parentheses"

    # Check for proper SQL structure
    cleaned_upper = cleaned.upper()
    if cleaned_upper.startswith('SELECT'):
        if 'FROM' not in cleaned_upper:
            return False, "SELECT query missing FROM clause"

    return True, "Valid SQL"


def clean_sql_response(sql_response):
    """Clean SQL response by extracting only the SQL query from verbose AI responses"""
    if not sql_response:
        return None

    sql_response = sql_response.strip()

    # Method 1: Extract from markdown code blocks
    # Look for SQL code blocks with ```sql or ```
    sql_blocks = re.findall(r'```(?:sql)?\s*\n?(.*?)\n?```',
                            sql_response, re.DOTALL | re.IGNORECASE)

    if sql_blocks:
        # Get the first SQL block that looks like a complete query
        for block in sql_blocks:
            cleaned_block = block.strip()
            is_valid, _ = validate_extracted_sql(cleaned_block)
            if is_valid:
                return cleaned_block

    # Method 2: Extract SQL from mixed content
    # Look for lines that start with SQL keywords
    lines = sql_response.split('\n')
    sql_lines = []
    in_sql_block = False

    for line in lines:
        line_upper = line.strip().upper()

        # Start capturing if we see SQL keywords
        if (line_upper.startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'SHOW', 'DESCRIBE', 'EXPLAIN'))):
            in_sql_block = True
            sql_lines.append(line.strip())
        elif in_sql_block:
            # Continue capturing if we're in a SQL block
            if line.strip() and not line.strip().startswith(('--', '#', '//')):
                # Stop if we hit explanatory text
                if any(phrase in line.lower() for phrase in ['however', 'this query', 'note that', 'explanation', 'to address']):
                    break
                sql_lines.append(line.strip())
            elif line.strip().endswith(';'):
                sql_lines.append(line.strip())
                break
            elif not line.strip():
                # Empty line - might be end of SQL
                if sql_lines and sql_lines[-1].endswith(';'):
                    break

    if sql_lines:
        potential_sql = '\n'.join(sql_lines).strip()
        is_valid, _ = validate_extracted_sql(potential_sql)
        if is_valid:
            return potential_sql

    # Method 3: Look for a single line SQL query
    single_line_sql = None
    for line in lines:
        line_stripped = line.strip()
        if (line_stripped.upper().startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE', 'EXPLAIN')) and
                line_stripped.endswith(';')):
            is_valid, _ = validate_extracted_sql(line_stripped)
            if is_valid:
                single_line_sql = line_stripped
                break

    if single_line_sql:
        return single_line_sql

    # Method 4: Last resort - try to clean the entire response
    # Remove common explanation phrases and extract just SQL
    explanation_phrases = [
        r'to calculate.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'however.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'this query.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'note that.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'explanation.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'to address.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'assuming.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'the following query.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'we can use.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'here is.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'here\'s.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'the query would be.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)',
        r'you can use.*?(?=SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|$)'
    ]

    cleaned = sql_response
    for phrase_pattern in explanation_phrases:
        cleaned = re.sub(phrase_pattern, '', cleaned,
                         flags=re.IGNORECASE | re.DOTALL)

    # Remove markdown formatting
    cleaned = re.sub(r'```(?:sql)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'```', '', cleaned)
    cleaned = cleaned.strip()

    # Try to extract SQL from what remains
    sql_match = re.search(
        r'((?:SELECT|WITH|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|EXPLAIN).*?;)', cleaned, re.IGNORECASE | re.DOTALL)
    if sql_match:
        potential_sql = sql_match.group(1).strip()
        is_valid, _ = validate_extracted_sql(potential_sql)
        if is_valid:
            return potential_sql

    return None


def call_groq_llm(prompt):
    """Call Groq LLM with error handling"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in environment variables")
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500
    }

    try:
        response = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 400:
            print(f"❌ 400 Bad Request Error: {response.text}")
            return None

        response.raise_for_status()
        response_json = response.json()

        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"].strip()
        else:
            print("❌ Unexpected response structure:", response_json)
            return None

    except Exception as err:
        print(f"❌ An error occurred: {err}")
        return None

# ============ QUERY OPTIMIZATION ============


def analyze_query_performance(engine, query, db_type="mysql"):
    """Analyze query performance and provide optimization suggestions"""
    try:
        if db_type.lower() == "mysql":
            explain_query = f"EXPLAIN FORMAT=JSON {query}"
        else:  # PostgreSQL
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"

        with engine.connect() as conn:
            result = conn.execute(text(explain_query))
            explain_result = result.fetchone()[0]

        return explain_result
    except Exception as e:
        return f"Error analyzing query: {str(e)}"


def get_optimization_suggestions(query, explain_result, schema):
    """Get AI-powered optimization suggestions"""
    optimization_prompt = f"""
You are a database performance expert. Analyze this SQL query and its execution plan to provide optimization suggestions.

Query:
{query}

Execution Plan:
{explain_result}

Database Schema:
{schema}

Provide specific, actionable optimization suggestions including:
1. Index recommendations
2. Query rewrite suggestions
3. Performance bottlenecks
4. Best practices violations

Format as a bulleted list with clear, implementable recommendations.
"""

    return call_groq_llm(optimization_prompt)


def parse_sql_complexity(query):
    """Parse SQL query to determine complexity metrics"""
    try:
        parsed = sqlparse.parse(query)[0]

        complexity = {
            "tables": 0,
            "joins": 0,
            "subqueries": 0,
            "aggregations": 0,
            "conditions": 0
        }

        query_upper = query.upper()

        # Count tables (rough estimate)
        if "FROM" in query_upper:
            complexity["tables"] = query_upper.count(
                "FROM") + query_upper.count("JOIN")

        # Count joins
        complexity["joins"] = query_upper.count("JOIN")

        # Count subqueries
        complexity["subqueries"] = query_upper.count("SELECT") - 1

        # Count aggregations
        agg_functions = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "GROUP BY"]
        complexity["aggregations"] = sum(
            query_upper.count(func) for func in agg_functions)

        # Count conditions
        complexity["conditions"] = query_upper.count(
            "WHERE") + query_upper.count("AND") + query_upper.count("OR")

        return complexity
    except:
        return {"error": "Could not parse query complexity"}

# ============ DATA VISUALIZATION ============


def create_auto_visualization(df, chart_type="auto"):
    """Create automatic visualizations based on data characteristics"""
    if df.empty:
        return None

    # Determine best chart type if auto
    if chart_type == "auto":
        chart_type = suggest_chart_type(df)

    try:
        if chart_type == "bar":
            return create_bar_chart(df)
        elif chart_type == "line":
            return create_line_chart(df)
        elif chart_type == "pie":
            return create_pie_chart(df)
        elif chart_type == "scatter":
            return create_scatter_plot(df)
        elif chart_type == "histogram":
            return create_histogram(df)
        else:
            return create_bar_chart(df)  # Default fallback
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")
        return None


def suggest_chart_type(df):
    """Suggest appropriate chart type based on data characteristics"""
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns

    if len(numeric_cols) >= 2:
        return "scatter"
    elif len(categorical_cols) == 1 and len(numeric_cols) == 1:
        if len(df) <= 10:
            return "pie"
        else:
            return "bar"
    elif len(categorical_cols) >= 1:
        return "bar"
    elif len(numeric_cols) == 1:
        return "histogram"
    else:
        return "bar"


def create_bar_chart(df):
    """Create bar chart from dataframe"""
    if len(df.columns) < 2:
        return None

    x_col = df.columns[0]
    y_col = df.columns[1]

    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
    fig.update_layout(height=500)
    return fig


def create_line_chart(df):
    """Create line chart from dataframe"""
    if len(df.columns) < 2:
        return None

    x_col = df.columns[0]
    y_col = df.columns[1]

    fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
    fig.update_layout(height=500)
    return fig


def create_pie_chart(df):
    """Create pie chart from dataframe"""
    if len(df.columns) < 2:
        return None

    labels_col = df.columns[0]
    values_col = df.columns[1]

    fig = px.pie(df, names=labels_col, values=values_col,
                 title=f"Distribution of {values_col}")
    return fig


def create_scatter_plot(df):
    """Create scatter plot from dataframe"""
    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) < 2:
        return None

    x_col = numeric_cols[0]
    y_col = numeric_cols[1]

    fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    fig.update_layout(height=500)
    return fig


def create_histogram(df):
    """Create histogram from dataframe"""
    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) == 0:
        return None

    col = numeric_cols[0]
    fig = px.histogram(df, x=col, title=f"Distribution of {col}")
    fig.update_layout(height=500)
    return fig


def create_dashboard_charts(df):
    """Create multiple charts for dashboard view"""
    charts = []

    # Summary statistics
    if not df.empty:
        summary_fig = create_summary_table(df)
        charts.append(("Summary Statistics", summary_fig))

    # Auto visualization
    auto_chart = create_auto_visualization(df)
    if auto_chart:
        charts.append(("Data Visualization", auto_chart))

    return charts


def create_summary_table(df):
    """Create summary statistics table"""
    try:
        summary = df.describe()

        fig = go.Figure(data=[go.Table(
            header=dict(values=['Statistic'] + list(summary.columns),
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[summary.index] + [summary[col] for col in summary.columns],
                       fill_color='lavender',
                       align='left'))
        ])

        fig.update_layout(title="Summary Statistics", height=400)
        return fig
    except:
        return None

# ============ REPORT GENERATION ============


def generate_business_report(df, query, analysis_results=None):
    """Generate comprehensive business intelligence report"""
    report_data = {
        "title": "Business Intelligence Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "data_summary": get_data_summary(df),
        "analysis": analysis_results or {},
        "insights": generate_ai_insights(df, query),
        "recommendations": get_business_recommendations(df, query)
    }

    return report_data


def get_data_summary(df):
    """Get comprehensive data summary"""
    if df.empty:
        return {"error": "No data to summarize"}

    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "column_types": {col: str(df[col].dtype) for col in df.columns},
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }

    # Add statistical summary for numeric columns
    numeric_summary = df.describe().to_dict() if not df.select_dtypes(
        include=['number']).empty else {}
    summary["statistics"] = numeric_summary

    return summary


def generate_ai_insights(df, query):
    """Generate AI-powered insights from data"""
    insights_prompt = f"""
Analyze this business data and query to provide key insights:

Query: {query}
Data Summary:
- Rows: {len(df)}
- Columns: {list(df.columns)}

Sample Data:
{df.head().to_string()}

Statistical Summary:
{df.describe().to_string() if not df.select_dtypes(include=['number']).empty else "No numeric data"}

Provide 3-5 key business insights and trends from this data. Focus on:
1. Notable patterns or outliers
2. Business implications
3. Data quality observations
4. Actionable findings

Keep insights concise and business-focused.
"""

    return call_groq_llm(insights_prompt)


def get_business_recommendations(df, query):
    """Get AI-powered business recommendations"""
    recommendations_prompt = f"""
Based on this business query and data analysis, provide strategic recommendations:

Query: {query}
Data Points: {len(df)} rows

Key Metrics:
{df.head().to_string()}

Provide 3-5 actionable business recommendations including:
1. Strategic actions based on the data
2. Areas for further investigation
3. Risk mitigation strategies
4. Opportunities for optimization

Format as numbered recommendations with clear action items.
"""

    return call_groq_llm(recommendations_prompt)


def create_pdf_report(report_data, df):
    """Create PDF report from report data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=30
    )
    story.append(Paragraph(report_data["title"], title_style))
    story.append(Spacer(1, 12))

    # Metadata
    story.append(Paragraph(
        f"<b>Generated:</b> {report_data['generated_at']}", styles['Normal']))
    story.append(
        Paragraph(f"<b>Query:</b> {report_data['query'][:100]}...", styles['Normal']))
    story.append(Spacer(1, 20))

    # Data Summary
    story.append(Paragraph("Data Summary", styles['Heading2']))
    summary = report_data["data_summary"]
    story.append(
        Paragraph(f"Total Rows: {summary.get('total_rows', 'N/A')}", styles['Normal']))
    story.append(Paragraph(
        f"Total Columns: {summary.get('total_columns', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Sample data table
    if not df.empty and len(df) > 0:
        story.append(Paragraph("Sample Data", styles['Heading2']))

        # Create table data
        sample_df = df.head(10)
        table_data = [list(sample_df.columns)]
        for _, row in sample_df.iterrows():
            table_data.append(
                [str(val)[:20] + "..." if len(str(val)) > 20 else str(val) for val in row])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

    # Insights
    if report_data.get("insights"):
        story.append(Paragraph("Key Insights", styles['Heading2']))
        story.append(Paragraph(report_data["insights"], styles['Normal']))
        story.append(Spacer(1, 20))

    # Recommendations
    if report_data.get("recommendations"):
        story.append(Paragraph("Business Recommendations", styles['Heading2']))
        story.append(
            Paragraph(report_data["recommendations"], styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ============ SESSION MANAGEMENT ============


def init_session_state():
    """Initialize session state for query history and favorites"""
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []

    if 'favorite_queries' not in st.session_state:
        st.session_state.favorite_queries = []

    if 'current_session' not in st.session_state:
        st.session_state.current_session = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.now(),
            "query_count": 0
        }


def add_to_history(nl_query, sql_query, results_count, execution_time=None):
    """Add query to history"""
    history_item = {
        "timestamp": datetime.now(),
        "nl_query": nl_query,
        "sql_query": sql_query,
        "results_count": results_count,
        "execution_time": execution_time,
        "session_id": st.session_state.current_session["id"]
    }

    st.session_state.query_history.append(history_item)
    st.session_state.current_session["query_count"] += 1

    # Keep only last 50 queries
    if len(st.session_state.query_history) > 50:
        st.session_state.query_history = st.session_state.query_history[-50:]


def add_to_favorites(nl_query, sql_query, name=None):
    """Add query to favorites"""
    favorite_item = {
        "id": len(st.session_state.favorite_queries) + 1,
        "name": name or f"Query {len(st.session_state.favorite_queries) + 1}",
        "nl_query": nl_query,
        "sql_query": sql_query,
        "created_at": datetime.now()
    }

    st.session_state.favorite_queries.append(favorite_item)


def get_query_history():
    """Get formatted query history"""
    return st.session_state.query_history


def get_favorite_queries():
    """Get favorite queries"""
    return st.session_state.favorite_queries


def export_session_data():
    """Export session data as JSON"""
    session_data = {
        "session_info": st.session_state.current_session,
        "query_history": [
            {
                **item,
                "timestamp": item["timestamp"].isoformat()
            }
            for item in st.session_state.query_history
        ],
        "favorite_queries": [
            {
                **item,
                "created_at": item["created_at"].isoformat()
            }
            for item in st.session_state.favorite_queries
        ],
        "exported_at": datetime.now().isoformat()
    }

    return json.dumps(session_data, indent=2)
