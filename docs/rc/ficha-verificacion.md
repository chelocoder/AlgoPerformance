# Ficha del instrumento y matriz de trazabilidad

**Nombre:** AlgoPerformance. **Versión:** v1.0.0-rc.2. **Objeto:** estimar tiempo transcurrido en ns por invocación reportada en condiciones reproducibles. **Entorno candidato:** Java 25 interpretado, Windows, P-core lógico 0. **Unidad de repetición independiente:** JVM. **Fuentes:** catálogo de 20 núcleos y generadores compartidos. **Estado:** candidato a revisión técnica y juicio de expertos.

## Catálogo

La referencia ejecutable es `rc/catalog.json`. Cada registro identifica el perfil, significado de n, región medida y resultado observable. La selección conserva siete clases.

| Clase | Núcleos |
|---|---|
| Θ(1) | Lectura por índice, diagonal |
| Θ(log n) | Binaria ausente, trayecto al montículo, ternaria ausente |
| Θ(n) | Suma, búsqueda lineal ausente, producto escalar |
| Θ(n log n) | Merge Sort, Heap Sort, lote de búsquedas binarias |
| Θ(n²) | Inserción inversa, Selection Sort, distancias por pares |
| Θ(n³) | Multiplicación densa, Floyd–Warshall, triángulos |
| Exponencial | Fibonacci Θ(φⁿ); Hanói y subconjuntos Θ(2ⁿ) |

## Requisitos y evidencias

| Requisito | Implementación | Evidencia |
|---|---|---|
| Selección, mallas, semillas y repeticiones | Catálogo, planificador Python y validación Java | Pruebas RC de configuración y 20 fixtures funcionales repetibles |
| Región medida y restauración | Fixture, Timer y verificación posterior | 244 comprobaciones Direct con reloj artificial y pruebas de núcleo |
| Validación de resultados, registros y exportación | Checksums, log por intento, CSV originales y consolidado | Pruebas sintéticas de validación/estadística y demostración rc.2 de siete JVM |
| Recuperación sin duplicar | Clave única SQLite, sello por intento y reanudación sólo de forks pendientes | Pruebas rc.2 de renombre, sello inválido, rollback y recuperación, evidencia previa de Job Object |
| Conservación y trazabilidad | Hash del JAR, hash de configuración y verificación del log | Registro local, archivos sellados e inventario SHA-256 del paquete |
| Validación externa | Paquete candidato e instrucciones reproducibles | Pendiente replicación en otro equipo y juicio de expertos |

