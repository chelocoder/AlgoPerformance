package pe.algoperformance.instrument.inputs;

import java.util.Arrays;
import java.util.Objects;
import java.util.SplittableRandom;

/** Genera un original reproducible fuera del intervalo de medición. */
public final class IntArrayGenerator {
    private IntArrayGenerator() {
    }

    public static IntArrayInput generate(
            int size, int minValue, int maxValue, IntArrayDistribution distribution,
            long seed, long payloadBudgetBytes) {
        Objects.requireNonNull(distribution, "distribution");
        if (minValue > maxValue) {
            throw new IllegalArgumentException("El mínimo de valores no puede superar al máximo.");
        }
        IntArrayInput.requireBudget(size, 1, payloadBudgetBytes);
        boolean distinct = distribution == IntArrayDistribution.STRICTLY_DESCENDING_DISTINCT
                || distribution == IntArrayDistribution.DISTINCT_PERMUTATION;
        long upperExclusive = (long) maxValue + 1;
        if (distinct && upperExclusive - minValue < size) {
            throw new IllegalArgumentException("El intervalo no permite generar tantos valores distintos.");
        }

        int[] values = new int[size];
        SplittableRandom random = new SplittableRandom(seed);
        if (distinct) {
            fillStrictlyDescending(values, minValue, upperExclusive, random);
            if (distribution == IntArrayDistribution.DISTINCT_PERMUTATION) {
                for (int i = values.length - 1; i > 0; i--) {
                    int selected = random.nextInt(i + 1);
                    int value = values[selected];
                    values[selected] = values[i];
                    values[i] = value;
                }
            }
        } else if (distribution == IntArrayDistribution.CONSTANT) {
            Arrays.fill(values, (int) random.nextLong(minValue, upperExclusive));
        } else {
            fillUniform(values, minValue, upperExclusive, random);
            if (distribution == IntArrayDistribution.ASCENDING
                    || distribution == IntArrayDistribution.DESCENDING) {
                Arrays.sort(values);
            }
            if (distribution == IntArrayDistribution.DESCENDING) {
                reverse(values);
            }
        }
        return new IntArrayInput(values);
    }

    static void fillUniform(int[] values, int minimum, long upperExclusive, SplittableRandom random) {
        for (int i = 0; i < values.length; i++) {
            values[i] = (int) random.nextLong(minimum, upperExclusive);
        }
    }

    private static void fillStrictlyDescending(
            int[] values, int minValue, long upperExclusive, SplittableRandom random) {
        // Elegir el máximo de un bloque consecutivo que cabe en el intervalo.
        long lowestMaximum = (long) minValue + values.length - 1;
        long maximum = random.nextLong(lowestMaximum, upperExclusive);
        for (int i = 0; i < values.length; i++) {
            values[i] = (int) (maximum - i);
        }
    }

    private static void reverse(int[] values) {
        for (int left = 0, right = values.length - 1; left < right; left++, right--) {
            int value = values[left];
            values[left] = values[right];
            values[right] = value;
        }
    }
}
