package pe.algoperformance.instrument.algorithms;

/** Montículo máximo con descenso por hueco hasta hoja y reinserción ascendente. */
public final class HeapSort {
    private HeapSort() {
    }

    public static void sort(int[] values) {
        for (int root = values.length / 2 - 1; root >= 0; root--) {
            restoreHeap(values, root, values.length);
        }
        for (int end = values.length - 1; end > 0; end--) {
            int maximum = values[0];
            values[0] = values[end];
            values[end] = maximum;
            restoreHeap(values, 0, end);
        }
    }

    private static void restoreHeap(int[] values, int root, int length) {
        int displaced = values[root];
        int hole = root;
        while (hole < length / 2) {
            int child = 2 * hole + 1;
            if (child + 1 < length && values[child + 1] > values[child]) {
                child++;
            }
            values[hole] = values[child];
            hole = child;
        }
        while (hole > root) {
            int parent = (hole - 1) / 2;
            if (values[parent] >= displaced) {
                break;
            }
            values[hole] = values[parent];
            hole = parent;
        }
        values[hole] = displaced;
    }
}
