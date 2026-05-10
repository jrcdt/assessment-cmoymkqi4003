import pandas as pd
import pytest

from app.agents.orchestrator import Orchestrator
from app.agents.validator import validate_business_rules


@pytest.mark.asyncio
async def test_validator_returns_expected_shape():
    """Smoke test — validator returns a dict with valid/errors keys."""
    df = pd.DataFrame()
    result = await validate_business_rules(df)

    assert isinstance(result, dict)
    assert "valid" in result
    assert "errors" in result


@pytest.mark.asyncio
async def test_validator_flags_negative_business_values():
    df = pd.DataFrame({"net_sales": [120, "-5"], "quantity": [2, "3"]})

    result = await validate_business_rules(df)

    assert result["valid"] is False
    assert any(error["rule"] == "non_negative_numeric" for error in result["errors"])


@pytest.mark.asyncio
async def test_validator_accepts_numeric_strings_and_mixed_dates():
    df = pd.DataFrame(
        {
            "net_sales": ["1,234.50", "1.234,50", "$99"],
            "created_at": ["2024-01-02", "02/01/2024", "2024-03-04T10:00:00Z"],
            "discount_pct": ["0", "15.5", "100"],
        }
    )

    result = await validate_business_rules(df)

    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_validator_flags_absurd_discount_percentage_and_bad_date():
    df = pd.DataFrame({"discount_pct": [150], "created_at": ["not-a-date"]})

    result = await validate_business_rules(df)

    assert result["valid"] is False
    assert {error["rule"] for error in result["errors"]} >= {"percentage_range", "date_parse"}


@pytest.mark.asyncio
async def test_validator_flags_discount_greater_than_amount():
    df = pd.DataFrame({"gross_sales": [100], "discount_amount": [120]})

    result = await validate_business_rules(df)

    assert result["valid"] is False
    assert any(error["rule"] == "discount_not_greater_than_base" for error in result["errors"])


@pytest.mark.asyncio
async def test_orchestrator_marks_suspicious_validation_results(monkeypatch):
    orchestrator = Orchestrator()

    async def fake_execute(_prompt):
        return {
            "success": True,
            "data": pd.DataFrame({"net_sales": [-1]}),
            "metadata": {"source": "test"},
        }

    monkeypatch.setattr(orchestrator.query_agent, "execute", fake_execute)

    result = await orchestrator.process_request("show sales")

    assert result["status"] == "success"
    assert result["validation_status"] == "suspicious"
    assert result["metadata"]["validation"][0]["passed"] is False