import pytest
import pandas as pd
from app.agents.validator import validate_business_rules


@pytest.mark.asyncio
async def test_validator_returns_expected_shape():
    """Smoke test — validator returns a dict with valid/errors keys."""
    df = pd.DataFrame()
    result = await validate_business_rules(df)
    assert isinstance(result, dict)
    assert "valid" in result
    assert "errors" in result
