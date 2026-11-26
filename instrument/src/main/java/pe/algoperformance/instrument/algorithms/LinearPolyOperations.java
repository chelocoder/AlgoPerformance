package pe.algoperformance.instrument.algorithms;

/** Reducciones y búsquedas con dominio numérico validado en la preparación. */
public final class LinearPolyOperations {
    private LinearPolyOperations() {
    }

    public static int linearSearch(int[] values, long target) {
        for (int i = 0; i < values.length; i++) {
            if (values[i] == target) {
                return i;
            }
        }
        return -1;
    }

    /** Los vectores tienen igual longitud y su dominio garantiza suma exacta en long. */
    public static long dotProduct(int[] left, int[] right) {
        if (left.length != right.length) {
            throw new IllegalArgumentException("Los vectores deben tener igual longitud.");
        }
        long sum = 0;
        for (int i = 0; i < left.length; i++) {
            sum += (long) left[i] * right[i];
        }
        return sum;
    }

    /** Una operación representa el lote completo de consultas ausentes. */
    public static long binarySearchBatch(int[] keys, long[] queries) {
        if (keys.length != queries.length) {
            throw new IllegalArgumentException("El lote requiere n claves y n consultas.");
        }
        long checksum = 0;
        for (long query : queries) {
            checksum += LogarithmicOperations.binarySearch(keys, query);
        }
        return checksum;
    }

    public static long pairDistanceSum(int[] values) {
        long sum = 0;
        for (int i = 0; i < values.length; i++) {
            for (int j = i + 1; j < values.length; j++) {
                sum += Math.abs((long) values[i] - values[j]);
            }
        }
        return sum;
    }
}
