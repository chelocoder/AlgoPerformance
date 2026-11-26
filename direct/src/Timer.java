package pe.algoperformance.direct;

import java.util.function.LongSupplier;

/** El reloj inyectable se usa exclusivamente para las pruebas funcionales. */
final class Timer {
    record Sample(long elapsed, long operations, long checksum, long parameter) {
        double nsPerOperation() { return (double) elapsed / operations; }
    }

    private final LongSupplier clock;
    private final long[] returns;

    Timer(LongSupplier clock, int operations) {
        this.clock = clock;
        returns = new long[operations];
    }

    Sample measure(Settings settings, Fixtures.Fixture fixture) {
        fixture.prepare().run();
        long parameter = fixture.parameter().getAsLong();
        var op = fixture.operation();
        long start;
        long elapsed;
        long checksum = 1;
        long operations = settings.operations();

        if (settings.algorithm().equals("control-clock")) {
            start = clock.getAsLong();
            elapsed = clock.getAsLong() - start;
        } else if (settings.windowMs() > 0) {
            operations = 0;
            start = clock.getAsLong();
            do {
                checksum = Fingerprint.mix(checksum, op.getAsLong());
                operations++;
                elapsed = clock.getAsLong() - start;
            } while (elapsed < settings.windowMs() * 1_000_000L);
        } else if (settings.algorithm().equals("control-loop")) {
            start = clock.getAsLong();
            for (int index = 0; index < returns.length; index++) {
                checksum = Fingerprint.mix(checksum, op.getAsLong());
            }
            elapsed = clock.getAsLong() - start;
        } else if (settings.mode() == Settings.Mode.BATCH) {
            start = clock.getAsLong();
            for (int index = 0; index < returns.length; index++) {
                returns[index] = op.getAsLong();
            }
            elapsed = clock.getAsLong() - start;
            checksum = Fingerprint.output(returns);
        } else {
            start = clock.getAsLong();
            long value = op.getAsLong();
            elapsed = clock.getAsLong() - start;
            checksum = value;
        }
        long result = fixture.result().getAsLong();
        fixture.finish().run();
        if (elapsed < 0) throw new IllegalStateException("Intervalo negativo");
        return new Sample(elapsed, operations, Fingerprint.mix(checksum, result), parameter);
    }
}

