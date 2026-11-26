package pe.algoperformance.instrument.algorithms;

/** Búsquedas por comparación y acumulación en el camino de un montículo. */
public final class LogarithmicOperations {
    private LogarithmicOperations() {
    }

    /** Devuelve el índice encontrado o el complemento del punto de inserción. */
    public static int binarySearch(int[] sortedKeys, long target) {
        int low = 0;
        int high = sortedKeys.length;
        while (low < high) {
            int mid = low + (high - low) / 2;
            int value = sortedKeys[mid];
            if (target == value) {
                return mid;
            }
            if (target < value) {
                high = mid;
            } else {
                low = mid + 1;
            }
        }
        return ~low;
    }

    /** Busca con dos pivotes y conserva el tercio que puede contener el objetivo. */
    public static int ternarySearch(int[] sortedKeys, long target) {
        int low = 0;
        int high = sortedKeys.length;
        while (low < high) {
            int third = (high - low) / 3;
            int left = low + third;
            int right = high - 1 - third;
            int a = sortedKeys[left];
            int b = sortedKeys[right];
            if (target == a) {
                return left;
            }
            if (target == b) {
                return right;
            }
            if (target < a) {
                high = left;
            } else if (target > b) {
                low = right + 1;
            } else {
                low = left + 1;
                high = right;
            }
        }
        return ~low;
    }

    /** Suma los nodos del camino desde un índice válido hasta la raíz incluida. */
    public static long heapRootSum(int[] heap, int index) {
        long sum = heap[index];
        while (index > 0) {
            index = (index - 1) / 2;
            sum += heap[index];
        }
        return sum;
    }
}
