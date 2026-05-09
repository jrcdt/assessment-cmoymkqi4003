# API Reference

## Anthropic Integration
El sistema utiliza el modelo `claude-3-5-sonnet` para tareas de razonamiento complejo y validación de datos. La latencia objetivo es < 2s para validaciones síncronas, así que cualquier llamada a Claude debe acotarse en tokens y tener un timeout explícito.

## Sistema multi-agente
El orquestador delega trabajo a agentes especializados (query, validation, etc.). La forma exacta en la que un nuevo agente se engancha al pipeline está en el código — revisa `app/utils/dispatcher.py` y `app/agents/orchestrator.py` para ver el patrón actual.
