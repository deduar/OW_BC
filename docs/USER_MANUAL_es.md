# OW_BC - Guía de Usuario

## ¿Qué es OW_BC?

OW_BC es una herramienta de **conciliación bancaria** que te ayuda a verificar que los pagos registrados en tus sistemas administrativos (como Fuerza Movil) coincidan correctamente con los movimientos en tu cuenta bancaria (Banesco).

**En resumen:** Subes tus estados de cuenta bancarios y tus reportes administrativos, y la aplicación te muestra qué transacciones coinciden automáticamente y cuáles necesitan revisión manual.

---

## Registro e Inicio de Sesión

### Registrarse
1. Haz clic en **"Register"**
2. Ingresa tu:
   - **Email** (será tu nombre de usuario)
   - **Contraseña** (mínimo 8 caracteres)
   - **Nombre de tu empresa/tenant**
3. Haz clic en **"Register"**

### Iniciar Sesión
1. Ingresa tu email y contraseña
2. Haz clic en **"Login"**

### Cerrar Sesión
- Haz clic en **"Logout"** en la esquina superior derecha

---

## Sección: Workspace (Espacio de Trabajo)

Esta es la pantalla principal donde realizas la conciliación.

### Subir Archivos

#### Subir Estado de Cuenta Bancario
1. En la sección **"Bank Statement Upload"**, haz clic en **"Select Files"**
2. Selecciona tu archivo de estado de cuenta (formatos: XLS, XLSX, CSV, PDF)
3. Haz clic en **"Upload"**
4. Espera a que el archivo se procese

**Archivos bancarios soportados:**
- Exportaciones de Banesco (formato XLS/HTML)
- Archivos CSV de otros bancos
- PDFs con movimientos bancarios

#### Subir Reporte Administrativo
1. En la sección **"Admin Report Upload"**, haz clic en **"Select File"**
2. Selecciona tu archivo de pagos (normalmente Excel de Fuerza Movil)
3. Haz clic en **"Upload"**

**Reportes administrativos soportados:**
- Archivos Excel de Fuerza Movil con detalle de pagos

### Archivos Subidos

En **"Uploaded Files"** puedes ver:

| Campo | Descripción |
|-------|-------------|
| **Filename** | Nombre del archivo |
| **Type** | "bank" (banco) o "admin" (administrativo) |
| **Status** | Estado del procesamiento |
| **Actions** | Botón para eliminar |

**Estados posibles:**
- `succeeded` - Procesado correctamente
- `pending` - En proceso
- `failed` - Error en el procesamiento
- `already_processed` - Archivo ya había sido procesado (no se duplicó)

### Selección de Archivos para Conciliación

1. **Bank Files**: Selecciona las casillas de los estados de cuenta a conciliar
2. **Admin File**: Selecciona el reporte administrativo a usar como referencia
3. Haz clic en **"Start Matching"**

**Importante:** Si subes el mismo archivo nuevamente, el sistema detectará que ya fue procesado y no lo procesará de nuevo.

---

## Sección: Run Details (Detalles de la Conciliación)

Después de iniciar una conciliación, aparece en la lista de **"Reconciliation Runs"**.

### Ver Detalles
- Haz clic en **"View Matches"** del run que quieras revisar

### Pestañas de Revisión

#### Pestaña "Matched" (Coincidencias)
Muestra transacciones que el sistema encontró automáticamente porque:
- La referencia del pago administrativo coincide con la referencia bancaria
- El monto coincide exactamente
- La fecha está dentro del rango aceptable

**Información mostrada para cada coincidencia:**

| Campo | Descripción |
|-------|-------------|
| **Fecha** | Fecha de la transacción |
| **Monto** | Cantidad de la transacción |
| **Referencia** | Número de referencia del pago |
| **Descripción** | Detalle de la transacción |

#### Pestaña "Suggested" (Sugerencias)
Muestra candidatos que podrían ser la misma transacción pero necesitan confirmación manual.

**Para cada sugerencia verás:**
- Información del registro bancario (izquierda)
- Información del registro administrativo (derecha)
- Puntuación de coincidencia (score)

**Acciones disponibles:**
- **Confirm** - Aceptar la coincidencia sugerida
- **Reject** - Descartar la sugerencia

#### Pestaña "Unmatched" (Sin Coincidencia)
Muestra transacciones que no encontraron ningún candidato para conciliar.

**Se divide en dos columnas:**
- **Bank Transactions** - Movimientos bancarios sin pareja
- **Admin Entries** - Pagos administrativos sin pareja

---

## Cómo Funciona la Concidencialción Automática

### Criterios de Coincidencia (en orden de importancia)

1. **Referencia** (más importante)
   - El sistema busca si la referencia del pago administrativo aparece dentro de la referencia del movimiento bancario
   - Ejemplo: Si el admin tiene referencia "52353" y el banco tiene "51362852353", coinciden

2. **Monto**
   - Los montos deben ser exactamente iguales

3. **Fecha**
   - Las fechas deben estar dentro de ±5 días

4. **Descripción**
   - Se compara la similitud del texto descriptivo

### Puntuación (Score)

- **Score ≥ 70**: Se marca automáticamente como "Matched"
- **Score < 70**: Se marca como "Suggested" (requiere confirmación manual)

---

## Exportar Resultados

Desde **Run Details**, haz clic en **"Export CSV"** para descargar un archivo CSV con:

- Todas las transacciones conciliadas (Matched)
- Todas las sugerencias
- Transacciones sin coincidencia (Unmatched)

El archivo incluye:
- Estado de cada match
- Score
- Fechas, montos y descripciones de ambos registros
- Tipo de decisión (automática o manual)

---

## Casos de Uso Comunes

### Caso 1: Primera Conciliación
1. Sube tu estado de cuenta bancario
2. Sube tu reporte de Fuerza Movil
3. Selecciona ambos archivos
4. Haz clic en "Start Matching"
5. Revisa las sugerencias y confírmalas o recházalas
6. Exporta los resultados

### Caso 2: Conciliación Mensual
1. Inicia sesión
2. Sube el nuevo estado de cuenta
3. Sube el nuevo reporte administrativo
4. Selecciona los archivos del mes
5. Realiza la conciliación

### Caso 3: Revisar Conciliaciones Anteriores
1. Ve a Workspace
2. Busca el Reconciliation Run que quieras revisar
3. Haz clic en "View Matches"
4. Revisa las pestañas según necesites

---

## Tips y Recomendaciones

### Antes de Conciliar
- Asegúrate de que los archivos estén completos y en el formato correcto
- Verifica que las fechas de ambos archivos correspondan al mismo período

### Durante la Revisión
- **Confirma** solo las sugerencias donde estés seguro que son la misma transacción
- **Rechaza** las sugerencias incorrectas
- Si una transacción bancaria no tiene coincidencia, puede deberse a:
  - Pago realizado en efectivo
  - Pago aún no procesado por el banco
  - Error en la referencia del pago

### Después de Conciliar
- Exporta siempre los resultados para tu registro
- Guarda una copia del CSV exportado

---

## Glosario

| Término | Significado |
|---------|-------------|
| **Bank Statement** | Estado de cuenta bancaria |
| **Admin Report** | Reporte administrativo (p.ej., Fuerza Movil) |
| **Match** | Transacción que coincide automáticamente |
| **Suggested** | Coincidencia potencial que necesita confirmación |
| **Unmatched** | Transacción sin candidato para conciliar |
| **Score** | Puntuación de confianza de la coincidencia |
| **Run** | Una ejecución de la conciliación |

---

## ¿Necesitas Ayuda?

Si tienes problemas técnicos:
- Verifica tu conexión a internet
- Asegúrate de usar la última versión de tu navegador
- Intenta limpiar la caché del navegador

Si el problema persiste, contacta al equipo de soporte con el **Run ID** del error.
