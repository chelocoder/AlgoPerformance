package pe.algoperformance.instrument.inputs;

/** Conserva el arreglo original y entrega copias independientes para preparar cada ejecución. */
public final class IntArrayInput {
    private final int[] original;

    // El generador cede la propiedad del arreglo recién asignado.
    IntArrayInput(int[] original) {
        this.original = original;
    }

    public int size() {
        return original.length;
    }

    public int valueAt(int index) {
        return original[index];
    }

    /** Comprueba el presupuesto de carga útil para el original y la nueva copia. */
    public int[] newWorkingCopy(long payloadBudgetBytes) {
        requireBudget(original.length, 2, payloadBudgetBytes);
        return original.clone();
    }

    /** Restaura un búfer existente sin asignar un arreglo nuevo. */
    public void resetWorkingCopy(int[] workingCopy) {
        if (workingCopy.length != original.length) {
            throw new IllegalArgumentException("El búfer debe tener el tamaño del original.");
        }
        System.arraycopy(original, 0, workingCopy, 0, original.length);
    }

    static void requireBudget(int size, int arrays, long budgetBytes) {
        // Límite conservador para el tamaño de arreglo en HotSpot.
        if (size <= 0 || size > Integer.MAX_VALUE - 8) {
            throw new IllegalArgumentException("Tamaño de arreglo inválido: " + size);
        }
        long requiredBytes = (long) size * Integer.BYTES * arrays;
        if (budgetBytes < requiredBytes) {
            throw new IllegalArgumentException("Presupuesto insuficiente: se requieren "
                    + requiredBytes + " bytes de carga útil.");
        }
    }
}
