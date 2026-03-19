# PRD: Sistema de Conciliación Bancaria Automática

## 1. Problema
- Los usuarios pasan horas conciliando manualmente datos de múltiples bancos (PDF, XLS, CSV) con un reporte CSV del sistema administrativo.
- Alto riesgo de errores y descuadres contables.

## 2. Objetivo
- Automatizar ≥85% de los emparejamientos.
- Reducir tiempo de conciliación semanal a <1 hora.

## 3. Requisitos Funcionales
- RF-001: Importar archivos de bancos en formato PDF, XLS y CSV.
- RF-002: Extraer y normalizar campos clave (fecha, monto, descripción, referencia).
- RF-003: Cargar reporte CSV del sistema administrativo.
- RF-004: Emparejar automáticamente transacciones por monto, fecha (±2 días) y descripción.
- RF-005: Mostrar lista de transacciones no conciliadas con sugerencias de coincidencia.
- RF-006: Permitir conciliación manual con un clic.

## 4. Requisitos No Funcionales
- RNF-001: Procesar 10,000 transacciones en menos de 5 minutos.
- RNF-002: Soportar 5 bancos iniciales.
- RNF-003: Exportar reporte de auditoría (conciliadas, pendientes, sugeridas).

## 5. Métricas de Éxito
- % de conciliaciones automáticas.
- Tiempo promedio de conciliación semanal.
- Número de errores contables reportados.