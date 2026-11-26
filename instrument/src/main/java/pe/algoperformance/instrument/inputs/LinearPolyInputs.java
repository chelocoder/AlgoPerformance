package pe.algoperformance.instrument.inputs;

import java.util.SplittableRandom;

/** Dominios y generadores de la fase 06B. */
public final class LinearPolyInputs {
    private LinearPolyInputs() {
    }

    public static void requireDotProductDomain(int n, int minimum, int maximum) {
        long magnitude = Math.max(Math.abs((long) minimum), Math.abs((long) maximum));
        requireProductFits(n, magnitude * magnitude);
    }

    public static void requirePairDistanceDomain(int n, int minimum, int maximum) {
        long pairs = (long) n * (n - 1) / 2;
        requireProductFits(pairs, (long) maximum - minimum);
    }

    private static void requireProductFits(long count, long maximumTerm) {
        if (maximumTerm != 0 && count > Long.MAX_VALUE / maximumTerm) {
            throw new IllegalArgumentException("El acumulador long puede desbordarse.");
        }
    }

    /** Usa n huecos distintos, incluido uno tras la última clave. */
    public static long[] missingQueries(int[] keys, long seed, long budgetBytes) {
        if (12L * keys.length > budgetBytes) {
            throw new IllegalArgumentException("Las claves y consultas exceden el presupuesto.");
        }
        long[] queries = new long[keys.length];
        for (int i = 0; i < keys.length; i++) {
            queries[i] = (long) keys[i] + 1;
        }
        var random = new SplittableRandom(seed).split();
        for (int i = queries.length - 1; i > 0; i--) {
            int selected = random.nextInt(i + 1);
            long value = queries[selected];
            queries[selected] = queries[i];
            queries[i] = value;
        }
        return queries;
    }
}
