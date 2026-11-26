package pe.algoperformance.instrument.algorithms;

/** Núcleos cúbicos sobre matrices cuadradas planas, almacenadas por filas. */
public final class CubicOperations {
    public static final long INFINITY = Long.MAX_VALUE / 2;

    private CubicOperations() {
    }

    /** Las entradas son distintas de la salida y el dominio asegura sumas exactas. */
    public static void multiply(int n, int[] left, int[] right, long[] output) {
        for (int i = 0; i < n; i++) {
            int row = i * n;
            for (int j = 0; j < n; j++) {
                long sum = 0;
                for (int k = 0; k < n; k++) {
                    sum += (long) left[row + k] * right[k * n + j];
                }
                output[row + j] = sum;
            }
        }
    }

    /** Diagonal cero, pesos no negativos, valores finitos menores que INFINITY. */
    public static void floydWarshall(int n, long[] distances) {
        for (int k = 0; k < n; k++) {
            for (int i = 0; i < n; i++) {
                int row = i * n;
                long toIntermediate = distances[row + k];
                for (int j = 0; j < n; j++) {
                    int index = row + j;
                    long candidate = toIntermediate + distances[k * n + j];
                    if (candidate < distances[index]) {
                        distances[index] = candidate;
                    }
                }
            }
        }
    }

    /** La adyacencia simétrica tiene valores 0 o 1 y diagonal cero. */
    public static long countTriangles(int n, byte[] adjacency) {
        long count = 0;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    count += adjacency[i * n + j] & adjacency[i * n + k] & adjacency[j * n + k];
                }
            }
        }
        return count;
    }
}
