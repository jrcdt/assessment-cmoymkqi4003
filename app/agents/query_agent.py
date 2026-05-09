from typing import Any, Dict

import pandas as pd


class QueryAgent:
    """
    Translates natural-language questions into SQL against the PostgreSQL
    warehouse and executes them.

    Stubbed for the simulation — returns an empty result shape so the
    orchestrator pipeline can be exercised end-to-end without standing
    up real LLM + DB infrastructure.
    """

    async def generate_sql(self, prompt: str, client_id: str) -> str:
        # Real implementation would dispatch to the LLM with the relevant
        # table schema as context and return generated SQL. The stub
        # returns a placeholder so callers can still assert on the shape.
        return "SELECT 1 AS placeholder"

    async def execute(self, prompt: str) -> Dict[str, Any]:
        # Stub — bypasses SQL generation/execution and returns an empty
        # DataFrame so downstream agents (orchestrator, validator) can be
        # developed and tested independently of the real pipeline.
        return {
            "success": True,
            "data": pd.DataFrame(),
            "metadata": {"source": "stub"},
        }
