package pe.algoperformance.instrument.catalog;

/** Etiquetas de las siete clases nominales del estudio. */
public enum ComplexityClass {
    CONSTANT("O(1)"),
    LOGARITHMIC("O(log n)"),
    LINEAR("O(n)"),
    LINEARITHMIC("O(n log n)"),
    QUADRATIC("O(n²)"),
    CUBIC("O(n³)"),
    EXPONENTIAL("O(cⁿ)");

    private final String label;

    ComplexityClass(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
