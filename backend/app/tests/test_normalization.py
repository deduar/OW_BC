from app.utils.normalization import parse_es_amount, parse_date, normalize_description, normalize_reference

def test_parse_es_amount():
    assert parse_es_amount("1.234,56") == 1234.56
    assert parse_es_amount("-25.973,02") == -25973.02
    assert parse_es_amount("79,20") == 79.20
    assert parse_es_amount("100") == 100.0
    assert parse_es_amount("") == 0.0

def test_parse_date():
    from datetime import datetime
    assert parse_date("18-07-2025") == datetime(2025, 7, 18)
    assert parse_date("18/07/2025") == datetime(2025, 7, 18)

def test_normalize_description():
    assert normalize_description("TPBW J0050205216   01080") == "j0050205216 01080"
    assert normalize_description("CR.I/REC 0191 J317467485") == "j317467485"
    assert normalize_description("MP *MERCADONA") == "mercadona"
    assert normalize_description("  multiple   spaces  ") == "multiple spaces"

def test_normalize_reference():
    assert normalize_reference("    4554") == "4554"
    assert normalize_reference("REF-123-ABC") == "123"
    assert normalize_reference("04249320499") == "04249320499"
    assert normalize_reference("") == ""
