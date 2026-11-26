package pe.algoperformance.direct;

import java.lang.management.ManagementFactory;
import java.util.Set;

/** Entrada del candidato interpretado. El arnés Direct histórico sigue sin cambios. */
public final class Candidate {
    private Candidate() {}

    public static void main(String[] args) {
        if (Runtime.version().feature() != 25
                || !ManagementFactory.getRuntimeMXBean().getInputArguments().contains("-Xint")) {
            throw new IllegalStateException("El candidato exige Java 25 con -Xint");
        }
        if (args.length == 0) throw new IllegalArgumentException("Falta acción");
        if (Set.of("list", "validate").contains(args[0])) {
            Worker.main(args);
            return;
        }
        Settings settings = Settings.parse(args, 1);
        if (Fixtures.isControl(settings.algorithm()) || settings.algorithm().equals("ring-buffer-enqueue")
                || settings.windowMs() != 0 || settings.mode() == Settings.Mode.COLD) {
            throw new IllegalArgumentException("Use un núcleo del catálogo principal y protocolo SINGLE o BATCH fijo");
        }
        switch (args[0]) {
            case "measure" -> {
                Worker.requireAffinity();
                Worker.run(settings, System.out);
            }
            case "expected" -> expected(settings);
            default -> throw new IllegalArgumentException("Acción no válida");
        }
    }

    private static void expected(Settings settings) {
        var fixture = Fixtures.create(settings);
        System.out.println(fixture.fingerprint());
        for (int iteration = 0; iteration < settings.warmups() + settings.measurements(); iteration++) {
            fixture.prepare().run();
            long parameter = fixture.parameter().getAsLong();
            long result = fixture.operation().getAsLong();
            long secondary = fixture.result().getAsLong();
            fixture.finish().run();
            boolean batch = iteration >= settings.warmups() && settings.mode() == Settings.Mode.BATCH;
            long checksum = result;
            if (batch) {
                checksum = 1;
                for (int index = 0; index < settings.operations(); index++) {
                    checksum = Fingerprint.mix(checksum, result);
                }
            }
            System.out.printf("%d,%d,%d%n", parameter, Fingerprint.mix(checksum, secondary),
                    batch ? settings.operations() : 1);
        }
    }
}
