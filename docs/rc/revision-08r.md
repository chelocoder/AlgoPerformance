# Levantamiento 08-R

| Observación | Resultado y evidencia |
|---|---|
| OBS-01 · README | Presenta primero Java 25 interpretado, configuración, medición y resultados. Las instrucciones JMH están en antecedentes. Los enlaces relativos del paquete se verifican antes de publicarlo. |
| OBS-02 · Recuperación | El sello se escribe en un archivo hermano y se sincroniza antes del renombre. SQLite confirma estado y clave de completitud en una transacción. Hay pruebas de interrupción antes del renombre o commit, sello ausente o truncado y reanudación sin duplicar el fork lógico. |
| OBS-03 · Completitud | Manifiesto JSON con campaña, versión, propósito, conteos esperados y válidos, pendientes y hashes. CSV etiquetados por estado. Prueba sintética parcial y manifestación completa observada en la demo. |
| OBS-04 · Semillas | El algoritmo puede sustituir semillas globales. Fibonacci y Hanói usan exclusivamente 42 nominal. Pruebas de sustitución, herencia, entradas inválidas y semillas nominales. |
| OBS-05 · Presupuestos | Límites globales y por subproceso en preparación y verificación, global y por JVM en medición. El registro separa duración por etapa. No se trasladaron los presupuestos JMH. |
| OBS-06 · Demostración | JSON de siete anclas, una por clase, con afinidad obligatoria. Están documentadas la topología, red y energía. Sin GUI. Las mediciones quedan etiquetadas como evidencia de demostración. |
| OBS-07 · Publicación | Se prepararon distribución limpia, instrucciones de release, auditoría local e inventario. Pendientes la revisión humana del historial, titularidad, autoría y autorización de difusión. |

## Verificación y demostración

La demostración utilizó Java Zulu 25.0.5.1+2-LTS con `-Xint`, P-core lógico 0 y máscara 0x1, red y Equilibrado. Terminó con siete JVM válidas, 14 calentamientos y 21 mediciones. El manifiesto declara siete forks esperados y completos, 21 mediciones esperadas y válidas y cero casos pendientes. Preparación **0,84 s**, verificación **0,80 s**, medición supervisada **2,42 s**. Se confirmó la liberación de la solicitud temporal de energía. La actividad externa quedó sin monitorización continua.

Las suites abarcan 82 pruebas Maven existentes, 244 comprobaciones Direct, 20 comprobaciones de fixtures deterministas sin reloj y 10 pruebas Python de rc.2. La simulación de rollback y reanudación usa archivos sintéticos. La demo real prueba recorrido completo y cobertura, sin inducir un corte duro. El piloto de rc.1, su JAR y su ZIP permanecen preservados. No se recopilaron datasets definitivos ni se entrenaron modelos.

## Estado de publicación

La referencia de trabajo sigue en `e2cf791f5b8630f504107da8104e3951f8bad75d`, con cambios locales pendientes. No se creó un commit o una etiqueta y no se añadió un remoto. El cribado del historial se limita a patrones en archivos de texto. Se elabora un informe local con hits sin exponer sus contenidos. Cotejar los hits, los metadatos de autores y las licencias antes de escribir en un remoto.

El candidato RC no empaqueta dependencias Java de terceros. Usa la biblioteca estándar de Python y el JDK local. El código Maven histórico requiere sus dependencias y avisos propios cuando se redistribuya. La propuesta Apache-2.0 y los nombres de autores quedan pendientes de aprobación. Los metadatos provisionales no atribuyen titularidad institucional.

Los registros de distribución se limitan a los archivos necesarios y al esquema de configuración. La evidencia medida se conserva por separado en el ZIP de revisión. Las rutas locales de los logs y planes se sustituyen por marcadores en la copia distribuida para revisión. Los originales locales y los datos numéricos siguen intactos.

## Dependencias y alcance del cribado

El cribado recorrió 18 commits. Señaló rutas locales en seis archivos históricos y un valor de correo de commit pendiente de revisar con su titular. No se detectaron los patrones incluidos de claves privadas o tokens. Se revisan coincidencias y permisos antes de publicar todo el historial. La distribución limpia utiliza una lista de inclusión independiente de Git.

En el POM histórico se identificaron JMH 1.37, Jackson Databind 2.21.4 y JUnit Jupiter 5.13.4. Verificar las licencias y avisos de ese módulo y sus dependencias transitivas si se publica su artefacto. El JAR de la distribución candidata no incorpora esas clases, el JDK ni instalaciones de Python.
