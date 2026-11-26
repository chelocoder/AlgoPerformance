# Manual de usuario · rc.2

Use Windows de 64 bits, PowerShell 7, Python 3.11 o posterior y JDK 25. La verificación se hizo con Azul Zulu 25.0.5.1+2 y Python 3.13. El coordinador utiliza la biblioteca estándar. En la raíz del proyecto o de la distribución:

```powershell
$env:ALGOPERFORMANCE_JDK_HOME = '<directorio JDK 25>'
.\rc\build.ps1 -Test
python rc/run.py plan rc/examples/demo-expertos.json
```

Si utiliza el JAR ya distribuido, puede omitir la compilación. `plan` prepara fixtures y muestra configuración, presupuestos y huellas, sin medir. El ejemplo `demo-expertos.json` cubre las siete clases con una JVM por algoritmo, dos calentamientos y tres mediciones. Cuando esté autorizado, use `python rc/run.py run rc/examples/demo-expertos.json`. Si el identificador ya existe, cambie el nombre para una nueva demostración o use `resume` con el JSON original para recuperar la ejecución.

## Configuración

| Campos JSON | Uso |
|---|---|
| `campaign`, `purpose` | Identidad y propósito del caso de uso |
| `forks`, `warmups`, `measurements` | JVM independientes y fases de cada una |
| `seeds` global | Lista reproducible, por defecto `[42]` |
| `algorithms[].seeds` | Sustituye la lista global del núcleo. Fibonacci y Hanói usan `[42]` nominal aunque el valor global difiera |
| `algorithms[].sizes` | Lista `values`, aritmética `start/step/count` o geométrica de razón entera `start/ratio/count` |
| `algorithms[].batch` | Invocaciones por intervalo, con lote unitario para estados destructivos o que reutilizan la salida |
| `preparation_timeout_s`, `preparation_case_timeout_s` | Límites de preparación global y por subproceso. Valores predeterminados 60 y 10 s |
| `verification_timeout_s`, `verification_case_timeout_s` | Límites de verificación funcional global y por subproceso. Predeterminados 120 y 30 s |
| `global_timeout_s`, `timeout_s` | Límites obligatorios de medición global y por JVM |

La demostración fija 45 s para preparación, 45 s para verificación y 70 s para medición. Estos límites pertenecen al uso de demostración en `-Xint`. El régimen y los tamaños de la campaña definitiva requieren otra aprobación. La afinidad permanece obligatoria. En un Windows sin P-core lógico 0, se puede revisar el plan y correr las pruebas funcionales. Esta versión carece de un modo de medición sin afinidad.

## Salida e interrupciones

Cada campaña tiene un directorio propio bajo `.local/phase08r/`. El manifiesto `export-<estado>-<id>.json` vincula ambos CSV por SHA-256 y enumera casos pendientes. Los nombres de los CSV incorporan el estado. Los tiempos de cada etapa figuran en `events.jsonl`.

Cree un archivo `STOP` en la carpeta de campaña para detenerse entre JVM. Tras revisar la causa, retire ese archivo y ejecute `python rc/run.py resume <configuración-original.json>`. Si quedó `active.lock` por corte abrupto, confirme primero que el coordinador y sus procesos terminaron. La reanudación conserva los intentos viejos e inicia únicamente forks sin una validación confirmada. `python rc/run.py export <configuración-original.json>` publica una exportación nueva de lo confirmado hasta ese momento.
