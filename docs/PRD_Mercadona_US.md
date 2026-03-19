# 📊 PRD: Sistema de Conciliación Bancaria Automática

## 🔍 Problem Statement
Los contadores pierden ~8h/semana conciliando manualmente transacciones de múltiples bancos (PDF, XLS, CSV) con un reporte CSV del sistema administrativo, lo que genera errores del 15% y riesgo financiero.

## 🎯 Objetivos
- Automatizar ≥85% de emparejamientos.
- Reducir tiempo de conciliación a <1h/semana.
- Eliminar errores por mala conciliación.

## 👥 User Persona
**María, Contadora Senior**  
- Trabaja en una empresa con 5 cuentas bancarias.  
- Usa Excel como hoja maestra.  
- Prioriza precisión y auditoría clara.

## 🧩 User Stories (Generadas con IA)
- **US-001**: Como usuario, quiero cargar archivos bancarios en PDF, XLS y CSV para centralizar los datos.  
- **US-002**: Como sistema, quiero normalizar descripciones (ej. “MP *MERCADONA” → “MERCADONA”) para mejorar el match.  
- **US-003**: Como usuario, quiero ver las transacciones no conciliadas con sugerencias de coincidencia (por monto, fecha ±2 días).  
- **US-004**: Como auditor, quiero exportar un reporte de conciliación con diferencias y acciones tomadas.

## 📈 Métricas de Éxito
- % de transacciones conciliadas automáticamente.  
- Tiempo promedio de conciliación semanal.  
- Número de errores contables relacionados.