package pe.algoperformance.instrument.algorithms;

import java.util.Objects;

/** Ordenamiento ascendente por división y conquista con búfer reutilizable. */
public final class MergeSort {
    private MergeSort() {
    }

    /**
     * Ordena en el mismo arreglo. Ambos arreglos deben ser no nulos.
     * El búfer debe ser distinto de la entrada y tener al menos su longitud.
     * La llamada reutiliza el búfer y puede sobrescribirlo.
     */
    public static void sort(int[] values, int[] workspace) {
        Objects.requireNonNull(values, "values");
        Objects.requireNonNull(workspace, "workspace");
        if (workspace == values || workspace.length < values.length) {
            throw new IllegalArgumentException("Se requiere un búfer independiente de longitud suficiente.");
        }
        sortRange(values, workspace, 0, values.length);
    }

    private static void sortRange(int[] values, int[] workspace, int start, int end) {
        if (end - start < 2) {
            return;
        }
        int middle = start + (end - start) / 2;
        sortRange(values, workspace, start, middle);
        sortRange(values, workspace, middle, end);
        merge(values, workspace, start, middle, end);
    }

    private static void merge(int[] values, int[] workspace, int start, int middle, int end) {
        System.arraycopy(values, start, workspace, start, end - start);
        int left = start;
        int right = middle;
        int output = start;
        while (left < middle && right < end) {
            if (workspace[left] <= workspace[right]) {
                values[output++] = workspace[left++];
            } else {
                values[output++] = workspace[right++];
            }
        }
        System.arraycopy(workspace, left, values, output, middle - left);
        output += middle - left;
        System.arraycopy(workspace, right, values, output, end - right);
    }
}
