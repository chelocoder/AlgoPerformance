package pe.algoperformance.direct;

import java.io.PrintStream;
import java.util.ArrayList;
import java.util.List;
import pe.algoperformance.instrument.catalog.AlgorithmCatalog;
import pe.algoperformance.instrument.runner.WindowsAffinity;

public final class Worker {
    private Worker() {}

    public static void main(String[] args) {
        if (args.length == 0) throw new IllegalArgumentException("Falta el comando del hijo");
        switch (args[0]) {
            case "list" -> AlgorithmCatalog.all().forEach(item -> System.out.println(item.id()));
            case "validate" -> {
                if (args.length < 2 || (args.length - 1) % 10 != 0) {
                    throw new IllegalArgumentException("Grupos de diez parámetros requeridos");
                }
                for (int index = 1; index < args.length; index += 10) {
                    var treatment = java.util.Arrays.copyOfRange(args, index, index + 10);
                    var settings = Settings.parse(treatment, 0);
                    System.out.println(settings.algorithm() + ":" + settings.size() + ":"
                            + Fixtures.create(settings).fingerprint());
                }
            }
            case "probe" -> {
                requireAffinity();
                Fixtures.create(Settings.parse(args, 1));
                System.out.println("probe_ok");
            }
            case "measure" -> {
                requireAffinity();
                run(Settings.parse(args, 1), System.out);
            }
            default -> throw new IllegalArgumentException("Comando del hijo desconocido");
        }
    }

    static void requireAffinity() {
        if (!"1".equals(System.getenv(WindowsAffinity.EXPECTED_MASK))) {
            throw new IllegalStateException("El hijo requiere la máscara supervisada 0x1");
        }
        WindowsAffinity.verify();
    }

    static void run(Settings settings, PrintStream output) {
        var fixture = Fixtures.create(settings);
        var timer = new Timer(System::nanoTime, settings.operations());
        List<Timer.Sample> warm = new ArrayList<>(settings.warmups());
        List<Timer.Sample> measured = new ArrayList<>(settings.measurements());
        boolean fixedScientificBatch = settings.mode() == Settings.Mode.BATCH
                && settings.windowMs() == 0 && !Fixtures.isControl(settings.algorithm());
        var warmSettings = fixedScientificBatch
                ? new Settings(settings.algorithm(), settings.size(), settings.seed(), settings.minimum(),
                        settings.maximum(), Settings.Mode.SINGLE, settings.warmups(), 1, 1, 0)
                : settings;
        var warmTimer = fixedScientificBatch ? new Timer(System::nanoTime, 1) : timer;
        output.printf("{\"event\":\"fixture\",\"pid\":%d,\"input_sha256\":\"%s\",\"jdk\":\"%s\"}%n",
                ProcessHandle.current().pid(), fixture.fingerprint(), Runtime.version());
        try {
            for (int index = 0; index < settings.warmups(); index++) {
                warm.add(warmTimer.measure(warmSettings, fixture));
            }
            for (int index = 0; index < settings.measurements(); index++) {
                measured.add(timer.measure(settings, fixture));
            }
        } finally {
            emit(output, "warmup", warm);
            emit(output, "measurement", measured);
        }
    }

    private static void emit(PrintStream output, String phase, List<Timer.Sample> samples) {
        for (int index = 0; index < samples.size(); index++) {
            var sample = samples.get(index);
            output.printf("{\"event\":\"sample\",\"phase\":\"%s\",\"iteration\":%d,"
                            + "\"operations\":%d,\"elapsed_ns\":%d,\"ns_per_operation\":%s,"
                            + "\"checksum\":%d,\"parameter\":%d}%n",
                    phase, index + 1, sample.operations(), sample.elapsed(),
                    sample.nsPerOperation(), sample.checksum(), sample.parameter());
        }
    }
}

