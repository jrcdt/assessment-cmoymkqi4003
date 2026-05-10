from typing import Dict, Any
from app.agents.query_agent import QueryAgent
from app.utils.logger import logger
from app.utils.dispatcher import dispatcher

class Orchestrator:
    def __init__(self):
        self.query_agent = QueryAgent()

    async def process_request(self, user_query: str) -> Dict[str, Any]:
        logger.info(f"Processing user query: {user_query}")

        # 1. Generate and execute SQL
        query_result = await self.query_agent.execute(user_query)

        if not query_result.get("success"):
            return {"error": "Failed to generate valid results"}

        dataset = query_result.get("data")

        # 2. Run post-query validators before returning results to the UI/API.
        # Validation failures do not block the response in this iteration; they
        # mark the payload as suspicious so callers can decide how to handle it.
        validation_results = await dispatcher.run_validators(dataset)
        is_suspicious = any(not result.get("passed", False) for result in validation_results)

        metadata = query_result.get("metadata") or {}
        metadata["validation"] = validation_results

        if is_suspicious:
            logger.warning("Query result marked as suspicious by validators")

        return {
            "status": "success",
            "data": dataset,
            "metadata": metadata,
            "validation_status": "suspicious" if is_suspicious else "passed",
        }