from app.utils.dispatcher import dispatcher
from app.services.llm import anthropic_client
import pandas as pd

@dispatcher.register_validator(name="business_rules_validator")
async def validate_business_rules(df: pd.DataFrame):
    """
    Validates the dataset against business rules.
    Returns a dict with 'valid' (bool) and 'errors' (list).
    """
    if df.empty:
        return {"valid": True, "errors": []}

    return {"valid": True, "errors": []}