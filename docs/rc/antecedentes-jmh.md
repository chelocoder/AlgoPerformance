# Antecedentes Java y JMH

Las fases anteriores usaron JMH 1.37 para probar arneses, perfiles y comportamiento experimental. Sus datos respaldan decisiones metodológicas, con dominios y presupuestos distintos del candidato interpretado. Direct rc.1 introdujo la recolección independiente con Java 25 y `-Xint`. Su piloto conserva 14 JVM, 70 calentamientos y 112 mediciones.

En el repositorio completo, el módulo Maven histórico se encuentra en `instrument/`. Desde ese directorio, `.\mvnw.cmd --version` identifica la herramienta y `.\mvnw.cmd -o -B -ntp test` ejecuta las pruebas si las dependencias ya están disponibles. Para reconstruirlo en un checkout separado, usar `.\mvnw.cmd -B clean package`. El clasificador `benchmarks` contiene el arnés y `java -jar <jar-histórico> -l` lista sus entradas. Conservar los hashes de los artefactos de referencia. La distribución del candidato se compila con `rc/build.ps1` y no requiere JMH o Maven.

El [informe rc.1](informe.md) describe la evidencia histórica. La cola circular permanece como caso metodológico complementario, separado del catálogo experimental principal.
