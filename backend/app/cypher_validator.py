"""
Cypher query validator — the critical safety layer.
Ensures LLM-generated queries are read-only and bounded.
"""

import re
from typing import NamedTuple

# ─── Dangerous keywords that indicate write operations ─────────────────────────
WRITE_KEYWORDS = [
    "CREATE", "MERGE", "DELETE", "DETACH DELETE", "SET", "REMOVE",
    "DROP", "LOAD CSV", "FOREACH", "CALL {",
]

# Write procedures that must be blocked
WRITE_PROCEDURES = [
    "db.createNode", "db.createRelationship",
    "apoc.create", "apoc.merge", "apoc.refactor",
    "apoc.periodic.commit", "apoc.periodic.iterate",
    "gds.graph.project", "gds.graph.drop",
]

# Max results to prevent resource exhaustion
DEFAULT_LIMIT = 100
MAX_LIMIT = 500


class ValidationResult(NamedTuple):
    is_valid: bool
    sanitized_query: str
    error: str | None


def validate_cypher(query: str) -> ValidationResult:
    """
    Validate a Cypher query for read-only safety.

    Returns:
        ValidationResult with is_valid flag, sanitized query, and error message.
    """
    if not query or not query.strip():
        return ValidationResult(False, "", "Empty query")

    normalized = query.strip()

    # ── Check for write keywords ──────────────────────────────────────────────
    # Tokenize to avoid false positives in string literals
    # Remove string literals before checking
    no_strings = re.sub(r"'[^']*'", "''", normalized)
    no_strings = re.sub(r'"[^"]*"', '""', no_strings)
    upper_no_strings = no_strings.upper()

    for keyword in WRITE_KEYWORDS:
        # Use word boundary matching to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, upper_no_strings):
            return ValidationResult(
                False, "",
                f"Query contains write operation: {keyword}. Only read-only queries are allowed."
            )

    # ── Check for write procedures ────────────────────────────────────────────
    for proc in WRITE_PROCEDURES:
        if proc.lower() in normalized.lower():
            return ValidationResult(
                False, "",
                f"Query contains write procedure: {proc}. Only read-only procedures are allowed."
            )

    # ── Check for CALL with subquery (can contain writes) ─────────────────────
    if re.search(r'\bCALL\s*\{', upper_no_strings):
        return ValidationResult(
            False, "",
            "CALL subqueries are not allowed as they can contain write operations."
        )

    # ── Check for semicolons (multi-statement injection) ──────────────────────
    # Remove semicolons inside string literals
    if ';' in no_strings:
        return ValidationResult(
            False, "",
            "Multiple statements (semicolons) are not allowed."
        )

    # ── Ensure query starts with a read keyword ───────────────────────────────
    first_keyword = upper_no_strings.lstrip().split()[0] if upper_no_strings.strip() else ""
    read_starts = {"MATCH", "OPTIONAL", "WITH", "UNWIND", "RETURN", "CALL", "USE"}
    if first_keyword not in read_starts:
        return ValidationResult(
            False, "",
            f"Query must start with a read operation (MATCH, RETURN, WITH, etc.), not '{first_keyword}'."
        )

    # ── Enforce LIMIT ─────────────────────────────────────────────────────────
    sanitized = normalized

    # Check if query already has a LIMIT
    limit_match = re.search(r'\bLIMIT\s+(\d+)', upper_no_strings)
    if limit_match:
        existing_limit = int(limit_match.group(1))
        if existing_limit > MAX_LIMIT:
            # Replace with max limit
            sanitized = re.sub(
                r'\bLIMIT\s+\d+',
                f'LIMIT {MAX_LIMIT}',
                sanitized,
                flags=re.IGNORECASE,
            )
    else:
        # Add a default LIMIT
        sanitized = sanitized.rstrip().rstrip(';')
        sanitized = f"{sanitized} LIMIT {DEFAULT_LIMIT}"

    return ValidationResult(True, sanitized, None)


def validate_and_prepare(query: str, timeout: float = 30.0) -> tuple[str, float]:
    """
    Validate query and return (sanitized_query, timeout).
    Raises ValueError if validation fails.
    """
    result = validate_cypher(query)
    if not result.is_valid:
        raise ValueError(result.error)

    # Cap timeout
    timeout = min(timeout, 60.0)

    return result.sanitized_query, timeout
