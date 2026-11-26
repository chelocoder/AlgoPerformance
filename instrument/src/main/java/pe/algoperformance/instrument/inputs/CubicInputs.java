package pe.algoperformance.instrument.inputs;

import java.util.SplittableRandom;
import pe.algoperformance.instrument.algorithms.CubicOperations;

/** Dimensionamiento y entradas reproducibles de las operaciones cúbicas. */
public final class CubicInputs {
    public static final int MULTIPLICATION_BYTES_PER_CELL = 16;
    public static final int FLOYD_BYTES_PER_CELL = 16;
    public static final int TRIANGLE_BYTES_PER_CELL = 1;

    private CubicInputs() {
    }

    public static int cells(int n, int bytesPerCell, long budget) {
        long square = (long) n * n;
        if (n < 1 || bytesPerCell < 1 || square > Integer.MAX_VALUE - 8
                || square > budget / bytesPerCell) {
            throw new IllegalArgumentException("Matriz no representable o fuera del presupuesto.");
        }
        return (int) square;
    }

    public static long cube(int n) {
        return Math.multiplyExact((long) n * n, n);
    }

    public static long triples(int n) {
        return n < 3 ? 0 : Math.multiplyExact((long) n * (n - 1), n - 2) / 6;
    }

    public static void requireProductDomain(int n, int min, int max) {
        long magnitude = Math.max(Math.abs((long) min), Math.abs((long) max));
        if (n < 1 || min > max || magnitude * magnitude > Long.MAX_VALUE / n) {
            throw new IllegalArgumentException("El acumulador de la matriz puede desbordarse.");
        }
    }

    public static void requireWeightDomain(int n, int min, int max) {
        if (n < 1 || min < 0 || min > max || Math.max(1L, n - 1L) * max >= CubicOperations.INFINITY) {
            throw new IllegalArgumentException("Pesos incompatibles con distancias finitas no negativas.");
        }
    }

    public static void requireAdjacencyDomain(int min, int max) {
        if (min != 0 || max != 1) {
            throw new IllegalArgumentException("La adyacencia del piloto requiere el intervalo [0, 1].");
        }
    }

    public static long[] distances(int n, int min, int max, long seed, long budget) {
        int cells = cells(n, FLOYD_BYTES_PER_CELL, budget);
        requireWeightDomain(n, min, max);
        var random = new SplittableRandom(seed);
        long[] weights = new long[cells];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i != j) {
                    weights[i * n + j] = random.nextLong(min, (long) max + 1);
                }
            }
        }
        return weights;
    }

    public static byte[] adjacency(int n, long seed, long budget) {
        int cells = cells(n, TRIANGLE_BYTES_PER_CELL, budget);
        var random = new SplittableRandom(seed);
        byte[] matrix = new byte[cells];
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                byte edge = (byte) random.nextInt(2);
                matrix[i * n + j] = edge;
                matrix[j * n + i] = edge;
            }
        }
        return matrix;
    }
}
