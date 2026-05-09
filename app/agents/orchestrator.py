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

        return {
            "status": "success",
            "data": dataset,
            "metadata": query_result.get("metadata")
        }