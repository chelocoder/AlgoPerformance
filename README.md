# AlgoPerformance · v1.0.0-rc.2

Instrumento candidato para recolectar tiempos de ejecución en una investigación doctoral sobre extrapolación con modelos matemáticos y de Machine Learning. Mide **20 algoritmos de siete clases** con **Java 25 en modo interpretado (`-Xint`)**. El tiempo se registra en nanosegundos por operación o por lote. Cada JVM es una réplica independiente.


> **Esta versión constituye un candidato a validación técnica y metodológica mediante juicio de expertos. Su publicación no implica la aprobación definitiva del instrumento ni la autorización para iniciar la recolección científica**.

## Finalidad y arquitectura

Investigación doctoral: «Modelado Predictivo Comparativo mediante Machine Learning para la Extrapolación del Tiempo de Ejecución de Algoritmos en Función del Tamaño de Entrada según su Complejidad Asintótica». Investigador principal: **Juan Marcelo Chamorro Avendaño**.

El coordinador Python expande la malla, supervisa una JVM Java 25 por fork y registra completitud y recuperación en SQLite. Java prepara la entrada, mide con `System.nanoTime()` y verifica los resultados tras el intervalo. La salida original y el agregado CSV se acompañan de un manifiesto con hashes y pendientes.

| Clase | Algoritmos |
|---|---|
| Θ(1) | Lectura por índice, diagonal |
| Θ(log n) | Búsqueda binaria ausente, trayecto al montículo, búsqueda ternaria ausente |
| Θ(n) | Suma, búsqueda lineal ausente, producto escalar |
| Θ(n log n) | Merge Sort, Heap Sort, lote de búsquedas binarias |
| Θ(n²) | Inserción inversa, Selection Sort, suma de distancias por pares |
| Θ(n³) | Multiplicación densa, Floyd–Warshall, conteo de triángulos |
| Exponencial | Fibonacci Θ(φⁿ), Hanói y subconjuntos Θ(2ⁿ) |

## Instalación y verificación rápida

Requisitos: Windows de 64 bits, PowerShell 7, Python 3.11 o superior y un JDK 25 local. La demostración con medición requiere un P-core lógico 0 disponible, máscara `0x1`, alimentación de red y plan Equilibrado. El plan y las pruebas funcionales se pueden revisar sin ejecutar mediciones.

```powershell
$env:ALGOPERFORMANCE_JDK_HOME = '<directorio del JDK 25>'
.\rc\build.ps1 -Test
python rc/run.py plan rc/examples/demo-expertos.json
```

Ejecute desde la raíz. La distribución también incluye el JAR compilado. En el [catálogo operativo](rc/catalog.json) se documentan los perfiles, las entradas y la operación de cada núcleo.

## Configurar, medir y exportar

El [ejemplo con tres mallas](rc/examples/config-tres-mallas.json) muestra listas, progresiones aritméticas y geométricas. Se pueden fijar tamaños, semillas globales o por algoritmo, número de JVM, intervalos por JVM y lote. Fibonacci y Hanói usan la semilla nominal 42. Consulte el [manual de usuario](docs/rc/manual-usuario.md) para límites y recuperación.

```powershell
# Demostración técnica. Ejecutar sólo si se cumplen las condiciones descritas.
python rc/run.py run rc/examples/demo-expertos.json
```

El CLI conserva los logs y los intentos en `.local/phase08r/<campaña>/`. Produce un CSV original por intervalo, un CSV consolidado y un manifiesto de exportación con conteos y hashes. Una exportación `partial` identifica los forks pendientes. Una exportación `complete` confirma la cobertura de esa configuración. Los resultados de la demostración son evidencia técnica ajena al dataset definitivo.

## Documentación y estado

La demostración de rc.2 verificó las siete clases con **7 JVM, 14 calentamientos y 21 mediciones válidas**. El piloto independiente de rc.1 conserva 112 mediciones. El candidato queda pendiente de juicio de expertos y autorización de publicación.

- [Manual técnico y protocolo](docs/rc/manual-tecnico.md)
- [Diccionario de datos](docs/rc/datos.md)
- [Ficha del instrumento y trazabilidad](docs/rc/ficha-verificacion.md)
- [Informe de levantamiento 08-R](docs/rc/revision-08r.md)
- [Antecedentes JMH](docs/rc/antecedentes-jmh.md)
- [Acceso y presentación para expertos](docs/validacion/presentacion-instrumento.md)
- [Historial de cambios](CHANGELOG.md) y [metadatos provisionales de cita](CITATION.cff)


## Recuperación, resultados y límites

Los intentos quedan preservados. Tras una interrupción, revise el registro y reanude con `resume` usando la misma configuración. El coordinador evita duplicar forks completos. Véanse la [demostración rc.2](examples/demo-rc2/README.md), el [manual](docs/rc/manual-usuario.md) y las [limitaciones](docs/rc/manual-tecnico.md). Se verificaron 82 pruebas Maven históricas, 244 comprobaciones Direct y 10 pruebas Python del candidato. La demostración de siete JVM es evidencia técnica limitada a ese equipo y esos tamaños. El modo interpretado, la topología y la granularidad del reloj condicionan la interpretación.

## Licencia y citación

[Apache License 2.0](LICENSE) para el código autorizado. Véase [NOTICE](NOTICE) para el alcance.

Chamorro Avendaño, J. M. (2026). *AlgoPerformance* (Versión 1.0.0-rc.2) [Software]. GitHub. https://github.com/chelocoder/AlgoPerformance
