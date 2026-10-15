"""Tests for the Cypher query validator — the most critical safety piece."""

import pytest
from app.cypher_validator import validate_cypher, validate_and_prepare


class TestValidateCypher:
    """Test suite for Cypher validation safety layer."""

    # ─── Valid Read Queries ────────────────────────────────────────────────────

    def test_simple_match_return(self):
        result = validate_cypher("MATCH (g:Gene) RETURN g")
        assert result.is_valid
        assert "LIMIT" in result.sanitized_query

    def test_match_with_where(self):
        result = validate_cypher("MATCH (g:Gene) WHERE g.symbol = 'BRCA1' RETURN g")
        assert result.is_valid

    def test_match_with_relationship(self):
        result = validate_cypher(
            "MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease) RETURN g, d"
        )
        assert result.is_valid

    def test_shortest_path(self):
        result = validate_cypher(
            "MATCH path = shortestPath((a:Gene {symbol:'BRCA1'})-[*]-(b:Disease)) RETURN path"
        )
        assert result.is_valid

    def test_with_clause(self):
        result = validate_cypher(
            "MATCH (g:Gene) WITH g ORDER BY g.symbol RETURN g"
        )
        assert result.is_valid

    def test_optional_match(self):
        result = validate_cypher(
            "OPTIONAL MATCH (g:Gene {symbol: 'BRCA1'})-[r]->(n) RETURN g, r, n"
        )
        assert result.is_valid

    def test_unwind(self):
        result = validate_cypher(
            "UNWIND ['BRCA1', 'TP53'] AS sym MATCH (g:Gene {symbol: sym}) RETURN g"
        )
        assert result.is_valid

    def test_count_aggregation(self):
        result = validate_cypher("MATCH (g:Gene) RETURN count(g) as total")
        assert result.is_valid

    def test_existing_limit_preserved(self):
        result = validate_cypher("MATCH (g:Gene) RETURN g LIMIT 10")
        assert result.is_valid
        assert "LIMIT 10" in result.sanitized_query

    def test_excessive_limit_capped(self):
        result = validate_cypher("MATCH (g:Gene) RETURN g LIMIT 99999")
        assert result.is_valid
        assert "LIMIT 500" in result.sanitized_query

    # ─── Write Operations Must Be Rejected ────────────────────────────────────

    def test_reject_create(self):
        result = validate_cypher("CREATE (g:Gene {symbol: 'EVIL'})")
        assert not result.is_valid
        assert "CREATE" in result.error

    def test_reject_merge(self):
        result = validate_cypher("MERGE (g:Gene {symbol: 'EVIL'})")
        assert not result.is_valid
        assert "MERGE" in result.error

    def test_reject_delete(self):
        result = validate_cypher("MATCH (g:Gene) DELETE g")
        assert not result.is_valid
        assert "DELETE" in result.error

    def test_reject_detach_delete(self):
        result = validate_cypher("MATCH (g:Gene) DETACH DELETE g")
        assert not result.is_valid
        assert "DETACH DELETE" in result.error or "DELETE" in result.error

    def test_reject_set(self):
        result = validate_cypher("MATCH (g:Gene {symbol:'BRCA1'}) SET g.evil = true RETURN g")
        assert not result.is_valid
        assert "SET" in result.error

    def test_reject_remove(self):
        result = validate_cypher("MATCH (g:Gene {symbol:'BRCA1'}) REMOVE g.name RETURN g")
        assert not result.is_valid
        assert "REMOVE" in result.error

    def test_reject_drop(self):
        result = validate_cypher("DROP INDEX ON :Gene(symbol)")
        assert not result.is_valid

    def test_reject_load_csv(self):
        result = validate_cypher("LOAD CSV FROM 'http://evil.com/data.csv' AS row CREATE (n {val: row[0]})")
        assert not result.is_valid

    def test_reject_foreach(self):
        result = validate_cypher("MATCH (g:Gene) FOREACH (x IN [1] | SET g.evil = true)")
        assert not result.is_valid

    # ─── Injection Prevention ─────────────────────────────────────────────────

    def test_reject_semicolon_injection(self):
        result = validate_cypher("MATCH (g:Gene) RETURN g; CREATE (evil:Evil)")
        assert not result.is_valid
        assert "semicolons" in result.error.lower() or "statements" in result.error.lower()

    def test_reject_call_subquery(self):
        result = validate_cypher("CALL { CREATE (n:Evil) } RETURN 1")
        assert not result.is_valid

    def test_reject_write_procedure(self):
        result = validate_cypher("CALL apoc.create.node(['Gene'], {symbol: 'EVIL'})")
        assert not result.is_valid

    # ─── String Literal Safety ────────────────────────────────────────────────

    def test_create_in_string_literal_allowed(self):
        """Words like CREATE inside string literals should NOT trigger rejection."""
        result = validate_cypher("MATCH (g:Gene) WHERE g.name CONTAINS 'CREATE' RETURN g")
        assert result.is_valid

    def test_delete_in_string_literal_allowed(self):
        result = validate_cypher("MATCH (g:Gene) WHERE g.name = 'DELETE this' RETURN g")
        assert result.is_valid

    # ─── Edge Cases ───────────────────────────────────────────────────────────

    def test_empty_query(self):
        result = validate_cypher("")
        assert not result.is_valid

    def test_whitespace_only(self):
        result = validate_cypher("   ")
        assert not result.is_valid

    def test_wrong_start_keyword(self):
        result = validate_cypher("INSERT INTO genes VALUES ('BRCA1')")
        assert not result.is_valid

    # ─── validate_and_prepare ─────────────────────────────────────────────────

    def test_validate_and_prepare_success(self):
        query, timeout = validate_and_prepare("MATCH (g:Gene) RETURN g")
        assert "LIMIT" in query
        assert timeout <= 60.0

    def test_validate_and_prepare_failure(self):
        with pytest.raises(ValueError):
            validate_and_prepare("CREATE (g:Gene {symbol: 'EVIL'})")

    def test_validate_and_prepare_timeout_cap(self):
        _, timeout = validate_and_prepare("MATCH (g:Gene) RETURN g", timeout=999)
        assert timeout == 60.0
