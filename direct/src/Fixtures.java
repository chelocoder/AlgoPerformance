package pe.algoperformance.direct;

import java.util.SplittableRandom;
import java.util.function.LongSupplier;
import pe.algoperformance.instrument.algorithms.*;
import pe.algoperformance.instrument.inputs.*;

/** Traduce los fixtures de los benchmarks a llamadas directas a las mismas fuentes científicas. */
final class Fixtures {
    private static final Runnable NONE = () -> {};
    private static final long MEMORY = Settings.BUDGET;

    record Fixture(Runnable prepare, LongSupplier operation, LongSupplier result, Runnable finish,
                   String fingerprint, LongSupplier parameter) {}

    static boolean isControl(String id) {
        return switch (id) {
            case "control-clock", "control-loop", "control-consume" -> true;
            default -> false;
        };
    }

    static boolean singleOnly(String id) {
        return switch (id) {
            case "ring-buffer-enqueue", "merge-sort", "heap-sort", "insertion-sort-reverse",
                 "selection-sort", "floyd-warshall", "dense-matrix-multiply", "hanoi-traversal" -> true;
            default -> false;
        };
    }

    static long payload(String id, int n) {
        return switch (id) {
            case "matrix-diagonal-sample" -> Math.multiplyExact(4L * n, n);
            case "dense-matrix-multiply", "floyd-warshall" -> Math.multiplyExact(16L * n, n);
            case "triangle-count-dense" -> (long) n * n;
            case "merge-sort", "binary-search-batch" -> 12L * n;
            case "array-sum", "heap-sort", "insertion-sort-reverse", "selection-sort", "dot-product" -> 8L * n;
            case "hanoi-traversal" -> 12L * n + 12;
            case "fibonacci-naive", "control-clock", "control-loop", "control-consume" -> 0;
            default -> 4L * n;
        };
    }

    /** Tamaños máximos registrados en los manifiestos de los pilotos anteriores. */
    static int pilotCeiling(String id) {
        return switch (id) {
            case "array-index-read", "linear-search-absent", "dot-product" -> 4_194_304;
            case "binary-search-absent", "heap-root-path" -> 4_194_303;
            case "ternary-search-absent" -> 4_782_969;
            case "array-sum" -> 10_000_000;
            case "merge-sort" -> 1_000_000;
            case "ring-buffer-enqueue" -> 1_048_576;
            case "heap-sort" -> 262_144;
            case "insertion-sort-reverse" -> 65_536;
            case "binary-search-batch" -> 32_768;
            case "selection-sort", "pair-distance-sum" -> 8_192;
            case "matrix-diagonal-sample" -> 4_096;
            case "triangle-count-dense" -> 384;
            case "floyd-warshall", "dense-matrix-multiply" -> 256;
            case "fibonacci-naive" -> 30;
            case "hanoi-traversal", "subset-enumeration" -> 22;
            default -> 1;
        };
    }

    static int[] uniform(Settings s, int n, long seed) {
        return ShortOperationInputs.uniform(n, s.minimum(), s.maximum(), seed, MEMORY);
    }

    static Fixture scalar(LongSupplier operation, Object... input) {
        return new Fixture(NONE, operation, () -> 0, NONE, Fingerprint.sha256(input), () -> 0);
    }

    static Fixture create(Settings s) {
        int n = s.size();
        long seed = s.seed();
        var random = new SplittableRandom(seed);
        var split = random.split();
        long[] parameter = new long[1];
        return switch (s.algorithm()) {
            case "array-index-read" -> {
                int[] values = uniform(s, n, seed);
                yield new Fixture(() -> parameter[0] = split.nextInt(n),
                        () -> ConstantOperations.read(values, (int) parameter[0]),
                        () -> 0, NONE, Fingerprint.sha256(values), () -> parameter[0]);
            }
            case "matrix-diagonal-sample" -> {
                int[] values = uniform(s, ShortOperationInputs.matrixCells(n, MEMORY), seed);
                yield scalar(() -> ConstantOperations.diagonalCorners(values), n, values);
            }
            case "ring-buffer-enqueue" -> {
                var ring = new IntRingBuffer(n);
                var values = new SplittableRandom(seed);
                yield new Fixture(() -> parameter[0] = values.nextLong(s.minimum(), (long) s.maximum() + 1),
                        () -> ring.enqueue((int) parameter[0]), () -> 0, () -> {
                            if (ring.dequeue() != parameter[0]) {
                                throw new IllegalStateException("Estado de la cola inválido");
                            }
                        }, Fingerprint.sha256(n, seed, s.minimum(), s.maximum()), () -> parameter[0]);
            }
            case "binary-search-absent", "ternary-search-absent" -> {
                int[] keys = ShortOperationInputs.orderedKeys(n, s.minimum(), s.maximum(), seed, MEMORY);
                var ternary = split.split();
                boolean binary = s.algorithm().equals("binary-search-absent");
                yield new Fixture(() -> {
                    long b = ShortOperationInputs.deepestMissingTarget(keys, split);
                    long t = ShortOperationInputs.aboveMaximum(keys, ternary);
                    parameter[0] = binary ? b : t;
                }, binary ? () -> LogarithmicOperations.binarySearch(keys, parameter[0])
                          : () -> LogarithmicOperations.ternarySearch(keys, parameter[0]),
                        () -> 0, NONE, Fingerprint.sha256(keys), () -> parameter[0]);
            }
            case "heap-root-path" -> {
                int[] values = ShortOperationInputs.heap(n, s.minimum(), s.maximum(), seed, MEMORY);
                yield new Fixture(() -> parameter[0] = ShortOperationInputs.deepestIndex(n, split),
                        () -> LogarithmicOperations.heapRootSum(values, (int) parameter[0]),
                        () -> 0, NONE, Fingerprint.sha256(values), () -> parameter[0]);
            }
            case "array-sum" -> {
                int[] values = generated(s, IntArrayDistribution.UNIFORM).newWorkingCopy(MEMORY);
                yield scalar(() -> ArraySum.sum(values), values);
            }
            case "linear-search-absent" -> {
                int[] values = uniform(s, n, seed);
                long target = (long) s.maximum() + 1;
                yield scalar(() -> LinearPolyOperations.linearSearch(values, target), values, target);
            }
            case "dot-product" -> {
                LinearPolyInputs.requireDotProductDomain(n, s.minimum(), s.maximum());
                int[] left = uniform(s, n, seed);
                int[] right = uniform(s, n, split.nextLong());
                yield scalar(() -> LinearPolyOperations.dotProduct(left, right), left, right);
            }
            case "binary-search-batch" -> {
                int[] keys = ShortOperationInputs.orderedKeys(n, s.minimum(), s.maximum(), seed, MEMORY);
                long[] queries = LinearPolyInputs.missingQueries(keys, seed, MEMORY);
                yield scalar(() -> LinearPolyOperations.binarySearchBatch(keys, queries), keys, queries);
            }
            case "merge-sort", "heap-sort", "insertion-sort-reverse", "selection-sort" -> sort(s);
            case "pair-distance-sum" -> {
                LinearPolyInputs.requirePairDistanceDomain(n, s.minimum(), s.maximum());
                int[] values = uniform(s, n, seed);
                yield scalar(() -> LinearPolyOperations.pairDistanceSum(values), values);
            }
            case "dense-matrix-multiply" -> {
                int cells = CubicInputs.cells(n, CubicInputs.MULTIPLICATION_BYTES_PER_CELL, MEMORY);
                CubicInputs.requireProductDomain(n, s.minimum(), s.maximum());
                int[] left = uniform(s, cells, seed);
                int[] right = uniform(s, cells, split.nextLong());
                long[] output = new long[cells];
                yield new Fixture(NONE, () -> {
                    CubicOperations.multiply(n, left, right, output);
                    return 0;
                }, () -> Fingerprint.output(output), NONE, Fingerprint.sha256(n, left, right), () -> 0);
            }
            case "floyd-warshall" -> {
                long[] original = CubicInputs.distances(n, s.minimum(), s.maximum(), seed, MEMORY);
                long[] working = new long[original.length];
                yield new Fixture(() -> System.arraycopy(original, 0, working, 0, working.length),
                        () -> {
                            CubicOperations.floydWarshall(n, working);
                            return 0;
                        }, () -> Fingerprint.output(working), NONE, Fingerprint.sha256(n, original), () -> 0);
            }
            case "triangle-count-dense" -> {
                CubicInputs.requireAdjacencyDomain(s.minimum(), s.maximum());
                byte[] edges = CubicInputs.adjacency(n, seed, MEMORY);
                yield scalar(() -> CubicOperations.countTriangles(n, edges), n, edges);
            }
            case "fibonacci-naive" -> {
                ExponentialOperations.requireSize(n, ExponentialOperations.MAX_FIBONACCI);
                yield scalar(() -> ExponentialOperations.fibonacci(n), n);
            }
            case "hanoi-traversal" -> {
                ExponentialInputs.requireHanoi(n, MEMORY);
                var tower = new HanoiTraversal(n);
                yield new Fixture(tower::restore, tower::solve, () -> 0, NONE, Fingerprint.sha256(n), () -> 0);
            }
            case "subset-enumeration" -> {
                ExponentialInputs.requireSubsets(n, MEMORY);
                int[] values = n == 0 ? new int[0] : uniform(s, n, seed);
                yield scalar(() -> ExponentialOperations.subsetSum(values), values);
            }
            case "control-clock" -> scalar(() -> seed, seed);
            case "control-loop", "control-consume" -> {
                long[] sequence = new long[s.operations()];
                for (int index = 0; index < sequence.length; index++) sequence[index] = split.nextLong();
                int[] cursor = {0};
                yield new Fixture(() -> cursor[0] = 0, () -> sequence[cursor[0]++],
                        () -> 0, NONE, Fingerprint.sha256(sequence), () -> 0);
            }
            default -> throw new IllegalArgumentException(s.algorithm());
        };
    }

    private static IntArrayInput generated(Settings s, IntArrayDistribution distribution) {
        return IntArrayGenerator.generate(s.size(), s.minimum(), s.maximum(), distribution, s.seed(), MEMORY);
    }

    private static Fixture sort(Settings s) {
        var distribution = switch (s.algorithm()) {
            case "merge-sort" -> IntArrayDistribution.UNIFORM;
            case "insertion-sort-reverse" -> IntArrayDistribution.STRICTLY_DESCENDING_DISTINCT;
            default -> IntArrayDistribution.DISTINCT_PERMUTATION;
        };
        var original = generated(s, distribution);
        int[] working = original.newWorkingCopy(MEMORY);
        String fingerprint = Fingerprint.sha256(working);
        Runnable sort = switch (s.algorithm()) {
            case "merge-sort" -> {
                int[] workspace = new int[s.size()];
                yield () -> MergeSort.sort(working, workspace);
            }
            case "insertion-sort-reverse" -> () -> InsertionSort.sort(working);
            case "heap-sort" -> () -> HeapSort.sort(working);
            default -> () -> SelectionSort.sort(working);
        };
        return new Fixture(() -> original.resetWorkingCopy(working), () -> {
            sort.run();
            return 0;
        }, () -> Fingerprint.output(working), NONE, fingerprint, () -> 0);
    }
}


