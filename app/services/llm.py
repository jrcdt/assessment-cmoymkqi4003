import os

import anthropic

from app.utils.logger import logger


class LLMService:
    """
    Wrapper service for Anthropic API calls.
    Handles communication with Claude models.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.default_model = "claude-3-5-sonnet-20240620"

    async def chat_completion(self, system_prompt: str, user_message: str) -> str:
        try:
            message = self.client.messages.create(
                model=self.default_model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise


# Singleton instance for use by other modules (e.g. app.agents.validator).
anthropic_client = LLMService()
