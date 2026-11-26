package pe.algoperformance.direct;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import pe.algoperformance.instrument.catalog.AlgorithmCatalog;
import pe.algoperformance.instrument.inputs.IntArrayDistribution;
import pe.algoperformance.instrument.inputs.IntArrayGenerator;

public final class FunctionalTest {
    private static int checks;
    private static void check(boolean condition) {
        if (!condition) throw new AssertionError("Comprobación " + (checks + 1));
        checks++;
    }

    public static void main(String[] args) {
        for (var algorithm : AlgorithmCatalog.all()) {
            int minimum = switch (algorithm.id()) {
                case "triangle-count-dense" -> 0;
                case "floyd-warshall" -> 1;
                default -> -100;
            };
            int maximum = algorithm.id().equals("triangle-count-dense") ? 1 : 100;
            var settings = new Settings(algorithm.id(), 8, 42, minimum, maximum,
                    Settings.Mode.SINGLE, 0, 1, 1, 0);
            var first = Fixtures.create(settings);
            var second = Fixtures.create(settings);
            check(first.fingerprint().equals(second.fingerprint()));
            for (int iteration = 0; iteration < 3; iteration++) {
                first.prepare().run();
                second.prepare().run();
                check(first.parameter().getAsLong() == second.parameter().getAsLong());
                long result = first.operation().getAsLong();
                check(result == second.operation().getAsLong());
                check(first.result().getAsLong() == second.result().getAsLong());
                switch (algorithm.id()) {
                    case "fibonacci-naive" -> check(result == 21);
                    case "ring-buffer-enqueue" -> check(result == 1);
                    case "array-index-read" -> check(result == Fixtures.uniform(settings, 8, 42)[(int) first.parameter().getAsLong()]);
                    case "binary-search-absent" -> {
                        int[] keys = pe.algoperformance.instrument.inputs.ShortOperationInputs.orderedKeys(
                                8, minimum, maximum, 42, Settings.BUDGET);
                        check(result == Arrays.binarySearch(keys, (int) first.parameter().getAsLong()));
                    }
                    case "linear-search-absent" -> check(result == -1);
                    case "merge-sort", "heap-sort", "selection-sort", "insertion-sort-reverse" -> {
                        var distribution = switch (algorithm.id()) {
                            case "merge-sort" -> IntArrayDistribution.UNIFORM;
                            case "insertion-sort-reverse" -> IntArrayDistribution.STRICTLY_DESCENDING_DISTINCT;
                            default -> IntArrayDistribution.DISTINCT_PERMUTATION;
                        };
                        int[] input = IntArrayGenerator.generate(8, minimum, maximum, distribution,
                                42, Settings.BUDGET).newWorkingCopy(Settings.BUDGET);
                        Arrays.sort(input);
                        check(first.result().getAsLong() == Fingerprint.output(input));
                    }
                    default -> {}
                }
                first.finish().run();
                second.finish().run();
            }
        }
        var batch = new Settings("array-index-read", 8, 42, -100, 100, Settings.Mode.BATCH, 0, 1, 3, 0);
        var calls = new ArrayList<String>();
        var fixture = new Fixtures.Fixture(() -> calls.add("prepare"), () -> {
            calls.add("invoke");
            return 5;
        }, () -> {
            calls.add("result");
            return 0;
        }, () -> calls.add("finish"), "test", () -> 0);
        long[] tick = {0};
        var timer = new Timer(() -> {
            calls.add("clock");
            return tick[0] += 30;
        }, 3);
        var sample = timer.measure(batch, fixture);
        check(calls.equals(List.of("prepare", "clock", "invoke", "invoke", "invoke", "clock", "result", "finish")));
        check(sample.operations() == 3 && sample.elapsed() == 30 && sample.nsPerOperation() == 10);
        calls.clear();
        var window = new Settings("array-index-read", 8, 42, -100, 100, Settings.Mode.BATCH, 0, 1, 1, 1);
        tick[0] = 0;
        var windowSample = new Timer(() -> tick[0] += 500000, 1).measure(window, fixture);
        check(windowSample.operations() == 2 && windowSample.elapsed() == 1000000);
        invalid(() -> new Settings("merge-sort", 8, 42, -100, 100, Settings.Mode.BATCH, 0, 1, 2, 0));
        invalid(() -> new Settings("array-index-read", 655360000, 42, -100, 100, Settings.Mode.SINGLE, 0, 1, 1, 0));
        invalid(() -> new Settings("fibonacci-naive", 8, 42, -100, 100, Settings.Mode.COLD, 1, 1, 1, 0));
        invalid(() -> new Settings("unknown", 8, 42, -100, 100, Settings.Mode.COLD, 0, 1, 1, 0));
        System.out.printf("Direct: %d comprobaciones funcionales aprobadas; ningún reloj real usado.%n", checks);
    }

    private static void invalid(Runnable action) {
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            checks++;
            return;
        }
        throw new AssertionError("Se esperaba validación");
    }
}
