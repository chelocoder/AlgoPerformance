# Diccionario de datos

## Original por intervalo

| Campos | Significado |
|---|---|
| campaign, config_id, version | ID de campaña, SHA-256 del JSON solicitado y versión del instrumento |
| algorithm, complexity, n, seed, profile | Identidad del núcleo, clase, tamaño, semilla y perfil |
| pid, fork, attempt | JVM real, réplica lógica y UUID del intento |
| phase, iteration | Calentamiento o medición, numeración 1 a k |
| operations, elapsed_ns, ns_per_operation | Invocaciones, tiempo total entero y tiempo amortizado |
| checksum, parameter | Observable verificado y selector efectivo cuando existe |
| mode, validation | SINGLE/BATCH y validación efectiva |

Un intervalo de lote aporta una fila. No se fabrican tiempos internos por invocación. `valid_resolution_zero` significa que el intervalo íntegro fue cero. El log y el índice preservan intentos con fallo y datos parciales que quedan fuera de filtros de completitud.

## Consolidado

Una fila por algoritmo, n, modo y cantidad de operaciones por intervalo dentro de una campaña. `representative_ns` es la media de intervalos por fork, media de forks por semilla y media de semillas con igual peso. Sólo incluye etapa de medición. `valid_measurements`, `seeds` y `forks` indican cobertura. `sd_ns`, `median_ns` y `cv_pct` describen los intervalos individuales; el CV usa su media aritmética y queda vacío si falta varianza muestral o su media no es positiva. `zero_measurements` cuenta ceros conservados. La dispersión entre JVM se estima sobre las medias por fork. Los ejemplos del paquete corresponden al piloto y quedan fuera de datasets definitivos.

## Manifiesto de exportación de rc.2

El JSON indica versión, campaña, propósito, hashes de la configuración y el artefacto, forks esperados y completados, mediciones esperadas y válidas, casos y forks pendientes y SHA-256 de ambos CSV. `complete` expresa cobertura del plan, mientras `partial` expresa faltantes. Ambos archivos aparecen con cabecera incluso si no existe ninguna observación validada. El propósito técnico de una demostración no cambia al completar la campaña.
