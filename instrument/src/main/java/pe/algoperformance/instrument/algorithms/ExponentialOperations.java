package pe.algoperformance.instrument.algorithms;

/** Recorridos exponenciales con cotas de ejecución explícitas. */
public final class ExponentialOperations {
    public static final int MAX_FIBONACCI = 34;
    public static final int MAX_BINARY_RECURSION = 22;

    private ExponentialOperations() {
    }

    public static void requireSize(int n, int limit) {
        if (n < 0 || n > limit) {
            throw new IllegalArgumentException("Tamaño fuera del límite computacional: " + n);
        }
    }

    public static long fibonacci(int n) {
        requireSize(n, MAX_FIBONACCI);
        return fibonacciRecursive(n);
    }

    private static long fibonacciRecursive(int n) {
        if (n < 2) {
            return n;
        }
        return fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
    }

    public static long subsetSum(int[] values) {
        requireSize(values.length, MAX_BINARY_RECURSION);
        return subsetsRecursive(values, 0, 0);
    }

    private static long subsetsRecursive(int[] values, int index, long sum) {
        if (index == values.length) {
            return sum;
        }
        return subsetsRecursive(values, index + 1, sum)
                + subsetsRecursive(values, index + 1, sum + values[index]);
    }
}
