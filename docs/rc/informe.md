# Informe de verificación técnica y piloto de repetibilidad

## Estado del repositorio

La auditoría inicial leyó la estructura, el estado de Git, los artefactos y los procesos Java activos. No se observaron procesos Java/Javaw al comprobarlos. La consulta de comandos mediante CIM quedó sin acceso. El directorio de ejecución del diagnóstico JMH 07-C no existía y ese diagnóstico no se inició. Sus preparativos permanecen aparte. La reorientación hacia Java interpretado usa Direct como recolector, sin reconstruir JAR históricos. El prototipo original y su copia de preservación se conservaron.

La referencia Git es `e2cf791f5b8630f504107da8104e3951f8bad75d`. No había remotos configurados. El candidato y su documentación quedan como cambios locales. No se creó commit, etiqueta, publicación ni push. El repositorio no aporta una licencia general identificada en su raíz. Propuesta para revisión institucional: evaluar Apache-2.0 para el código, previa confirmación de titularidad y requisitos de la universidad. La publicación de datos y documentación requiere una decisión separada. Se deben confirmar el autor institucional y los metadatos de la cita antes de difundirla.

## Componentes y pruebas

Se recuperaron 20 núcleos, generadores, catálogo, Direct, JDK experimental, supervisor Windows y pruebas previas. `rc/` añade entrada interpretada, catálogo operativo, CLI de configuración y planificación, comprobación de observables, persistencia SQLite, CSV y ejemplos. El JAR se construye con `javac --release 25` y sólo clases necesarias del instrumento. La distribución del paquete incluye el binario para réplica y las fuentes para reconstrucción. Se usó JDK Azul Zulu 25.0.5.1+2-LTS y el entorno Windows con alimentación de red y Equilibrado.

- 82 pruebas Maven pasaron en el árbol científico.
- 244 comprobaciones Direct se ejecutaron bajo `-Xint` con reloj artificial donde correspondía.
- 20 núcleos se comprobaron en JVM interpretadas mediante fixtures reproducibles con dos verificaciones funcionales por núcleo y sin reloj.
- 5 pruebas Python del candidato cubrieron mallas, selección, consolidación, validación, cero instrumental y reanudación de un intento sellado con rechazo de duplicación.
- El protocolo de recuperación de 07-C tiene pruebas y evidencia de timeout sintético con Job Object. Es un antecedente independiente. El piloto RC no interrumpió deliberadamente sus JVM.

## Piloto técnico real

`pilot-rc-xint-01` se ejecutó una vez. Los casos se fijaron antes de medir. 7 algoritmos, una ancla por clase, dos JVM por algoritmo, semilla 42, cinco calentamientos y ocho mediciones por JVM. Fueron 14 JVM, 70 calentamientos y 112 mediciones válidas. Se observaron cero intervalos de tiempo igual a cero. El tiempo de pared entre inicio y cierre del supervisor fue 4,591 s. Se comprobó la máscara 0x1 por JVM y la liberación temporal de suspensión.

| Algoritmo | n | Modo y lote | Media jerárquica (ns/op) | CV entre 2 JVM |
|---|---:|---|---:|---:|
| Lectura por índice | 64 | BATCH 64 | 47,754 | 7,81 % |
| Binaria ausente | 63 | BATCH 32 | 173,828 | 11,12 % |
| Suma | 1 000 | BATCH 8 | 5 568,750 | 2,50 % |
| Merge Sort | 1 000 | SINGLE | 328 537,500 | 1,86 % |
| Inserción inversa | 100 | SINGLE | 37 618,750 | 1,67 % |
| Multiplicación densa | 32 | SINGLE | 526 956,250 | 10,61 % |
| Fibonacci | 10 | SINGLE | 2 456,250 | 0,36 % |

Dos JVM permiten una observación preliminar de repetibilidad, con incertidumbre elevada. La búsqueda binaria tuvo el mayor CV entre JVM de este piloto. La multiplicación densa tuvo la mayor dispersión relativa agrupando intervalos, aproximadamente 23,58 %. La distinción importa porque las ocho iteraciones no son ocho JVM independientes. El piloto no constituye calibración metrológica, validación de todo el dominio ni juicio de expertos. Sus CSV son ejemplos de datos reales de prueba y quedan fuera de la recolección definitiva.

## Límites y preparación de publicación

El modo interpretado cambia el régimen experimental. Antes de la muestra definitiva se requiere justificar dominios, presupuesto, calentamiento y lotes adecuados a ese régimen. Los tamaños, duraciones y criterios de la propuesta JMH 07-C no se trasladan automáticamente. Falta repetir instalación y prueba en un entorno independiente, estudiar estabilidad a escala y ampliar la evidencia de recuperación ante corte duro. El mecanismo de reanudación por fork y el Job Object no sustituyen verificación de respaldo y copia de resultados.

Para publicar: confirmar licencia y titularidad, autoría de CITATION, revisar dependencias y escanear todo el historial antes de autorizar difusión. El ZIP de revisión utiliza una lista de inclusión. Excluye directorios históricos privados, credenciales, SQLite con rutas locales y cachés. Las copias textuales de evidencia sustituyen las rutas absolutas locales mediante marcadores. Los originales permanecen en el equipo. No se autoriza publicar el ZIP ni la rama desde esta fase.
