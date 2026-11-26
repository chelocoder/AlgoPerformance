package pe.algoperformance.instrument.inputs;

import java.util.SplittableRandom;

/** Entradas de los seis casos breves. Todas las reservas se validan antes de asignar. */
public final class ShortOperationInputs {
    private ShortOperationInputs() {
    }

    public static int matrixCells(int side, long budgetBytes) {
        if (side < 2) {
            throw new IllegalArgumentException("El lado debe ser al menos dos.");
        }
        long cells = (long) side * side;
        if (cells > Integer.MAX_VALUE - 8 || cells > budgetBytes / Integer.BYTES) {
            throw new IllegalArgumentException("La matriz excede la representación o el presupuesto.");
        }
        return (int) cells;
    }

    public static int[] uniform(int size, int minimum, int maximum, long seed, long budgetBytes) {
        IntArrayInput.requireBudget(size, 1, budgetBytes);
        if (minimum > maximum) {
            throw new IllegalArgumentException("Intervalo de valores inválido.");
        }
        int[] values = new int[size];
        IntArrayGenerator.fillUniform(values, minimum, (long) maximum + 1, new SplittableRandom(seed));
        return values;
    }

    public static int[] heap(int size, int minimum, int maximum, long seed, long budgetBytes) {
        int[] values = uniform(size, minimum, maximum, seed, budgetBytes);
        for (int child = 1; child < size; child++) {
            values[child] = Math.min(values[child], values[(child - 1) / 2]);
        }
        return values;
    }

    public static int deepestIndex(int size, SplittableRandom random) {
        return random.nextInt(Integer.highestOneBit(size) - 1, size);
    }

    public static boolean hasSpacedKeys(int size, int minimum, int maximum) {
        return (long) maximum - minimum >= 2L * (size - 1);
    }

    public static int[] orderedKeys(int size, int minimum, int maximum, long seed, long budgetBytes) {
        IntArrayInput.requireBudget(size, 1, budgetBytes);
        if (!hasSpacedKeys(size, minimum, maximum)) {
            throw new IllegalArgumentException("Intervalo insuficiente para claves y huecos.");
        }
        long first = new SplittableRandom(seed).nextLong(minimum, (long) maximum - 2L*(size-1) + 1);
        int[] keys = new int[size];
        for (int i = 0; i < size; i++) {
            keys[i] = (int) (first + 2L*i);
        }
        return keys;
    }

    /** Elige una hoja externa de profundidad máxima para la misma partición binaria. */
    public static long deepestMissingTarget(int[] keys, SplittableRandom random) {
        int low = 0;
        int high = keys.length;
        while (low < high) {
            int mid = low + (high - low) / 2;
            int leftDepth = Integer.SIZE - Integer.numberOfLeadingZeros(mid - low);
            int rightDepth = Integer.SIZE - Integer.numberOfLeadingZeros(high - mid - 1);
            if (leftDepth > rightDepth || leftDepth == rightDepth && random.nextBoolean()) {
                high = mid;
            } else {
                low = mid + 1;
            }
        }
        return low == 0 ? (long) keys[0] - 1 : (long) keys[low - 1] + 1;
    }

    public static long aboveMaximum(int[] keys, SplittableRandom random) {
        return (long) keys[keys.length - 1] + random.nextInt(1, 1025);
    }
}
