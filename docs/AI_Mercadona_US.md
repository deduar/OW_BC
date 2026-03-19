# Quality Guard: Validación del Problema
Antes de escribir el PRD, se verifica que el problema esté bien definido en tres dimensiones:

## ✅ 1.1. Métricas con baseline y target
Baseline:
8 horas/semana por contador en conciliación manual.
30% de transacciones requieren revisión manual.
15% de errores contables detectados mensualmente.
Target:
Reducir tiempo a <1 hora/semana.
Automatizar ≥85% de emparejamientos.
Eliminar errores contables por mala conciliación.

## ✅ 1.2. Observaciones de campo (Gemba Walk)
"Tengo que abrir 5 archivos distintos: dos en PDF, uno en Excel, y dos en CSV. Los copio a mano a una hoja maestra." – Contador, Sucursal Lima.
"A veces el banco aplica comisiones con un día de retraso y no coinciden las fechas." – Asistente administrativo.
Se observó que el 40% de los errores ocurren por diferencias de formato en descripciones (ej. “PAGO MERCADO PAGO” vs “MP *MERCADONA”).

## ✅ 1.3. Impacto cuantificado
Ahorro anual estimado: 8h/semana × 50 semanas = 400h/año × $30/h = $12,000/año en productividad.
Reducción de riesgo: Evitar multas por errores contables (estimado: $5,000/año).

# Research & JTBD: Validación del Problema
Se aplica el Mom Test para evitar soluciones asumidas:

❌ "¿Te gustaría una herramienta que lea PDFs automáticamente?" → Pregunta sesgada.
✅ "¿Cómo haces la conciliación hoy? ¿Qué pasos tomas cuando un pago no coincide? ¿Qué herramientas usas?" → Revela comportamiento real.
Job-to-be-Done (JTBD) validado:

"Como contador, cuando recibo extractos bancarios en múltiples formatos, quiero emparejarlos automáticamente con mis registros contables, para evitar errores y ahorrar tiempo en tareas repetitivas."

