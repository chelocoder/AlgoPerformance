package pe.algoperformance.instrument.algorithms;

/** Selección convencional por mínimo en cada sufijo. */
public final class SelectionSort {
    private SelectionSort() {
    }

    public static void sort(int[] values) {
        for (int i = 0; i < values.length - 1; i++) {
            int minimum = i;
            for (int j = i + 1; j < values.length; j++) {
                if (values[j] < values[minimum]) {
                    minimum = j;
                }
            }
            if (minimum != i) {
                int value = values[i];
                values[i] = values[minimum];
                values[minimum] = value;
            }
        }
    }
}
