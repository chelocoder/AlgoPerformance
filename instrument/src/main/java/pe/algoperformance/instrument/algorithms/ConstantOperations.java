package pe.algoperformance.instrument.algorithms;

/** Operaciones con entrada preasignada y coste independiente de su tamaño. */
public final class ConstantOperations {
    private ConstantOperations() {
    }

    public static int read(int[] values, int index) {
        return values[index];
    }

    /** La matriz cuadrada no vacía se representa linealmente por filas. */
    public static long diagonalCorners(int[] matrix) {
        return (long) matrix[0] + matrix[matrix.length - 1];
    }
}
