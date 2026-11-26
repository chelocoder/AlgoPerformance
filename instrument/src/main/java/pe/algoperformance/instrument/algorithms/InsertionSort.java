package pe.algoperformance.instrument.algorithms;

/** Ordenamiento ascendente por desplazamiento e inserción en el prefijo ordenado. */
public final class InsertionSort {
    private InsertionSort() {
    }

    /**
     * Ordena en el mismo arreglo, que debe ser no nulo. Admite claves repetidas.
     * El caso experimental de peor costo usa claves distintas en orden descendente.
     */
    public static void sort(int[] values) {
        for (int index = 1; index < values.length; index++) {
            int key = values[index];
            int position = index;
            while (position > 0 && values[position - 1] > key) {
                values[position] = values[position - 1];
                position--;
            }
            values[position] = key;
        }
    }
}
