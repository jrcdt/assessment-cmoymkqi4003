from typing import Dict, Any

from app.agents.query_agent import QueryAgent
from app.utils.logger import logger
from app.utils.dispatcher import dispatcher


FRIENDLY_VALIDATION_MESSAGE = (
    "Los resultados fueron generados correctamente, pero detectamos posibles "
    "inconsistencias en los datos. Te recomendamos revisarlos antes de tomar decisiones."
)


class Orchestrator:
    def __init__(self):
        self.query_agent = QueryAgent()

    async def process_request(self, user_query: str) -> Dict[str, Any]:
        logger.info(f"Processing user query: {user_query}")

        # 1. Generate and execute SQL
        query_result = await self.query_agent.execute(user_query)

        if not query_result.get("success"):
            logger.warning("QueryAgent failed to generate valid results")

            return {
                "status": "error",
                "error": {
                    "code": "QUERY_FAILED",
                    "message": "No pudimos generar resultados para tu consulta. Intenta reformularla.",
                },
                "data": None,
                "metadata": {},
                "validation_status": "not_run",
            }

        dataset = query_result.get("data")
        metadata = query_result.get("metadata") or {}

        # 2. Run post-query validators before returning results to the UI/API.
        # Validation failures do not block the response in this iteration.
        # Technical validation details are kept in metadata/logs, while the user
        # receives only a friendly message.
        try:
            validation_results = await dispatcher.run_validators(dataset)
        except Exception as exc:
            logger.exception("Validator dispatch failed unexpectedly")

            metadata["validation"] = {
                "status": "failed",
                "internal_error": str(exc),
            }

            return {
                "status": "success",
                "data": dataset,
                "metadata": metadata,
                "validation_status": "suspicious",
                "user_message": FRIENDLY_VALIDATION_MESSAGE,
            }

        is_suspicious = any(
            not result.get("passed", False)
            for result in validation_results
        )

        metadata["validation"] = {
            "status": "suspicious" if is_suspicious else "passed",
            "results": validation_results,
        }

        if is_suspicious:
            logger.warning(
                "Query result marked as suspicious by validators",
                extra={"validation_results": validation_results},
            )

        response: Dict[str, Any] = {
            "status": "success",
            "data": dataset,
            "metadata": metadata,
            "validation_status": "suspicious" if is_suspicious else "passed",
        }

        if is_suspicious:
            response["user_message"] = FRIENDLY_VALIDATION_MESSAGE

        return response