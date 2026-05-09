import functools
from typing import Callable, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Dispatcher:
    def __init__(self):
        self.validators: Dict[str, Callable] = {}

    def register_validator(self, name: str):
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self.validators[name] = wrapper
            logger.info(f"Validator '{name}' registered successfully.")
            return wrapper
        return decorator

    async def run_validators(self, data: Any) -> List[Dict[str, Any]]:
        results = []
        for name, validator in self.validators.items():
            try:
                res = await validator(data)
                results.append({"validator": name, "passed": res.get("valid", False), "errors": res.get("errors", [])})
            except Exception as e:
                logger.error(f"Error running validator {name}: {e}")
                results.append({"validator": name, "passed": False, "errors": [str(e)]})
        return results

dispatcher = Dispatcher()