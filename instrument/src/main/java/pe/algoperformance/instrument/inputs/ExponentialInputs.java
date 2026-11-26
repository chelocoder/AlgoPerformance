package pe.algoperformance.instrument.inputs;

import pe.algoperformance.instrument.algorithms.ExponentialOperations;

/** Validaciones compartidas por el plan y los estados JMH. */
public final class ExponentialInputs {
    private ExponentialInputs() {
    }

    public static void requireHanoi(int n, long budget) {
        ExponentialOperations.requireSize(n, ExponentialOperations.MAX_BINARY_RECURSION);
        requirePayload(12L * n + 12, budget);
    }

    public static void requireSubsets(int n, long budget) {
        ExponentialOperations.requireSize(n, ExponentialOperations.MAX_BINARY_RECURSION);
        requirePayload(4L * n, budget);
    }

    private static void requirePayload(long bytes, long budget) {
        if (bytes > budget) {
            throw new IllegalArgumentException("La carga útil exponencial excede el presupuesto.");
        }
    }
}
