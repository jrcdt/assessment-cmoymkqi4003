# Especificación del Validator Agent (Borrador)

## Contexto
El dashboard ha estado mostrando resultados imposibles a clientes — combinaciones de datos que violan reglas básicas de dominio que nuestros analistas dan por sentadas pero que no están codificadas en ningún lado del pipeline. El `QueryAgent` está produciendo SQL sintácticamente válido, pero la calidad de los datos en las tablas legacy y la ausencia de una capa de validación de dominio hacen que filas inválidas lleguen al usuario. Necesitamos una capa que se ejecute después del SQL y antes de devolver los resultados a la UI.

## Restricciones no funcionales
- **Latencia**: el overhead añadido p95 debería mantenerse por debajo de ~2 segundos. Cualquier llamada a LLM debe estar acotada (timeout explícito).
- **Manejo de fallos**: un timeout o error transitorio del LLM no debería tumbar la request completa de manera silenciosa. Definir y documentar el fallback (permitir / bloquear / marcar como parcial) antes de mergear.
- **Parsing**: la data legacy es inconsistente. Los campos numéricos a veces llegan como strings y las fechas en distintos formatos. El validador no debería crashear ante esto.

## Preguntas abiertas
El set exacto de reglas de negocio a enforzar en esta primera iteración aún se está alineando con el equipo. El punto de integración con el orquestador existente también es parte de la conversación — vale la pena entender la utilidad de dispatching que ya existe en el repo antes de decidir el wiring.

## Fuera de alcance (para esta iteración)
- Backfill de datos históricos que ya entraron malos.
- Mostrar errores de validación directamente en la UI de Chainlit. Por ahora loguear y marcar el resultado como sospechoso a nivel del API.
