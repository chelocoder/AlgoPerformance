package pe.algoperformance.instrument.algorithms;

/** Suma lineal de enteros con acumulación en long. */
public final class ArraySum {
    private ArraySum() {
    }

    /**
     * Recorre el arreglo completo sin modificarlo. El arreglo debe ser no nulo.
     * Para un arreglo vacío devuelve cero.
     */
    public static long sum(int[] values) {
        long total = 0;
        for (int value : values) {
            total += value;
        }
        return total;
    }
}
