# Manual técnico y protocolo de medición

## Arquitectura

El coordinador Python valida JSON, expande mallas y ejecuta Java 25 con `-Xint -Xmx256m`. Usa el supervisor Windows aprobado para afinidad, tiempo, cancelación del árbol y solicitud temporal de energía. La entrada Candidate reutiliza los núcleos y generadores de `instrument/`, los adaptadores de `direct/` y el reloj de Direct. Se compila como JAR independiente sin clases JMH. Los JAR previos se preservan.

## Región y correctitud

1. Verificar P-core, red y plan. Validar ambiente, configuración, tamaño y memoria. Calcular una referencia funcional por tamaño/semilla fuera de cualquier medición.
2. Crear una JVM nueva por fork. Comprobar la máscara antes del calentamiento y preparar el fixture con semilla reproducible. Preparar el selector por intervalo y restaurar los mutables fuera del reloj.
3. Cronometrar mediante dos lecturas de `System.nanoTime()`. SINGLE captura una llamada. BATCH cronometra las llamadas sobre estado no destructivo y almacena los retornos escalares en un búfer preasignado. El bucle y el almacenamiento son parte del intervalo amortizado.
4. Después del reloj, obtener checksum. Para arreglos y matrices se lee el resultado completo tras el cierre. Comparar parámetros y checksums de cada intervalo con una referencia no cronometrada del mismo núcleo. Las pruebas de núcleo usan además oráculos funcionales. La referencia de campaña detecta alteraciones de fixture, estado o parámetros y tiene alcance limitado para detectar un error sistemático del núcleo compartido.
5. Escribir logs y resultados fuera del intervalo. Validar PID, máscara, huella, cobertura exacta, signo, tipo, operación y cálculo ns/op. Conservar todos los extremos válidos. Mantener los ceros en escala natural.

El calentamiento del lote fijo usa invocaciones individuales. El modo interpretado es parte del estimando, igual que el tamaño de lote y el perfil. No equiparar los resultados con los históricos JMH. No afirmar que el modo interpretado elimina efectos de planificación, caché, GC o granularidad del reloj.

## Persistencia y validación

SQLite tiene una clave única por caso/fork dentro de la campaña. El sello se serializa a un archivo hermano temporal, se sincroniza y se publica por renombre atómico. Al detectar un sello faltante o truncado se preserva el intento y se conserva la posición como pendiente. La inserción de completitud y actualización del estado se confirman en la misma transacción. Los logs crudos se conservan aunque falte salida. Antes de consolidar, se verifican SHA-256 de cada original y de la validación. Tras una interrupción, un resultado ya sellado puede reconciliarse al reanudar tras cotejarlo con el log y el fixture esperado. Un intento sin sello se conserva como incompleto y una reanudación solicitada registra un nuevo intento. Los datos de prueba sintéticos sólo viven en directorios temporales. El modo exportación puede devolver un subconjunto de forks completos en un estado parcial. El manifiesto indica completitud, pendientes y SHA-256 de ambos CSV. La demostración conserva su propósito técnico aun cuando está completa. La preparación de fixtures, la verificación funcional y la medición tienen presupuestos y duraciones separados.

## Limitaciones y compatibilidad

El piloto verifica el trayecto de extremo a extremo en Windows, un equipo y una JVM por réplica. La disponibilidad de CPU, límites de memoria y tiempos de `-Xint` deben revisarse de nuevo para escalas definitivas. El control de límites se apoya en el Job Object, el coordinador y cotas por fixture de Direct. El CLI limita ejecuciones nuevas a 20 000 JVM y exige dividir diseños mayores. Falta validar en otra instalación, fijar el protocolo definitivo de tamaños y cerrar la evaluación por expertos.

