# QAgent Core Orchestrator

Bienvenido al equipo de QAgent SpA. Este es el motor principal de nuestro copiloto de decisiones. El servicio se encarga de transformar lenguaje natural en consultas SQL precisas y devolver resultados accionables.

## Estructura del Proyecto

- `app/agents/`: Definición de agentes especializados (Query, Validator, etc.).
- `app/utils/dispatcher.py`: Registro y despacho de herramientas para el sistema multi-agente.
- `app/services/llm.py`: Cliente unificado para modelos de lenguaje.
- `docs/`: Documentación técnica y especificaciones de arquitectura.

## Configuración Rápida

1. Clona el repositorio y crea un entorno virtual.
2. Copia el archivo de variables de entorno:
   bash
   cp .env.example .env
   
3. Instala las dependencias y corre el servidor en modo desarrollo:
   bash
   pip install -r requirements.txt
   fastapi dev app/main.py
   

## Tu Equipo

- **Matías Oyarzún** — Tech Lead & Engineering Manager
- **Diego Méndez** — Senior Backend & AI Engineer
- **Valentina Rojas** — Data Engineer Senior

## Flujo de Trabajo

Revisa el archivo `docs/issues/402-validator-agent.md` para detalles sobre tu primera tarea. Una vez que tengas una solución, abre un Pull Request para que Diego o Valentina lo revisen.