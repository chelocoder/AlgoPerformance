# Presentación del instrumento para juicio de expertos

**Investigación doctoral:** «Modelado Predictivo Comparativo mediante Machine Learning para la Extrapolación del Tiempo de Ejecución de Algoritmos en Función del Tamaño de Entrada según su Complejidad Asintótica».

**Investigador:** Juan Marcelo Chamorro Avendaño. **Instrumento:** AlgoPerformance v1.0.0-rc.2.

> Esta versión constituye un candidato a validación técnica y metodológica mediante juicio de expertos. Su publicación no implica la aprobación definitiva del instrumento ni la autorización para iniciar la recolección científica.

## Finalidad y operación

El instrumento registra el tiempo transcurrido por operación científica y sus condiciones de ejecución. Cada JVM independiente realiza calentamiento y medición mediante Java 25 interpretado. Se registran algoritmo, clase, tamaño n, semilla, fork, intervalo, lote, nanosegundos por operación y observable. El coordinador Python prepara el plan y supervisa un proceso Java por réplica. SQLite e intentos sellados separan las ejecuciones válidas y pendientes. [Arquitectura y protocolo](../rc/manual-tecnico.md) · [Catálogo de 20 algoritmos](../../rc/catalog.json).

La preparación, restauración y comprobación quedan fuera del reloj. Los lotes se usan para operaciones compatibles y producen una fila por intervalo. Las salidas son CSV original, consolidado y manifiesto de integridad. [Diccionario de datos](../rc/datos.md).

## Evidencia y límites

Pasaron 82 pruebas Maven históricas, 244 comprobaciones Direct, 10 pruebas Python y verificaciones funcionales de los 20 núcleos. La demostración rc.2 completó siete JVM, 14 calentamientos y 21 intervalos válidos. La prueba de repetibilidad preliminar de rc.1 conservó 14 JVM y 112 intervalos. El rango de CV entre las dos JVM de cada caso de ese piloto fue 0,36 %–11,12 %. Ninguna prueba permite generalizar a otros tamaños o equipos. No hubo calibración metrológica ni juicio de expertos. [Ficha y trazabilidad](../rc/ficha-verificacion.md) · [Informe previo de repetibilidad](../rc/informe.md) · [Datos de ejemplo](../../examples/demo-rc2/README.md).

## Acceso

Solicite acceso al repositorio privado. Una vez aceptada una invitación, consulte la prerelease, descargue la distribución y el manifiesto SHA-256, y siga el [manual de usuario](../rc/manual-usuario.md). Se requiere Windows de 64 bits, JDK 25, Python 3.11 o superior y PowerShell 7. La medición requiere P-core lógico 0, máscara 0x1, red y Equilibrado. La planificación puede verificarse sin iniciar mediciones. No se asignan evaluadores ni se registran valoraciones en este documento.

## Referencia APA 7

Chamorro Avendaño, J. M. (2026). *AlgoPerformance* (Versión 1.0.0-rc.2) [Software]. GitHub. https://github.com/chelocoder/AlgoPerformance
