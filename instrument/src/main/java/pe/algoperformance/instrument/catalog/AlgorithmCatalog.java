package pe.algoperformance.instrument.catalog;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;

/** Registro ordenado de variantes científicas candidatas. */
public final class AlgorithmCatalog {
    private static final List<AlgorithmDescriptor> ENTRIES = List.of(
            implemented("array-index-read", "Lectura por índice",
                    "Lee una posición válida.", "Longitud del arreglo",
                    ComplexityClass.CONSTANT, "Θ(1)",
                    AnalysisCase.ANY, "valid-index"),
            implemented("ring-buffer-enqueue", "Inserción en cola circular",
                    "Inserta sin redimensionar.", "Capacidad de la cola",
                    ComplexityClass.CONSTANT, "Θ(1)",
                    AnalysisCase.ANY, "ring-with-free-slot"),
            implemented("matrix-diagonal-sample", "Muestreo de la diagonal",
                    "Suma las dos esquinas de la diagonal principal.", "Lado de la matriz",
                    ComplexityClass.CONSTANT, "Θ(1)",
                    AnalysisCase.ANY, "preallocated-matrix"),
            implemented("binary-search-absent", "Búsqueda binaria sin acierto",
                    "Reduce el intervalo a la mitad hasta probar la ausencia.", "Número de claves ordenadas",
                    ComplexityClass.LOGARITHMIC, "Θ(log n)",
                    AnalysisCase.WORST_CASE, "distinct-keys-absent-target"),
            implemented("heap-root-path", "Trayecto a la raíz",
                    "Suma valores desde un nodo de la última profundidad.", "Número de nodos del montículo",
                    ComplexityClass.LOGARITHMIC, "Θ(log n)",
                    AnalysisCase.DEEPEST_LEVEL, "heap-deepest-node"),
            implemented("ternary-search-absent", "Búsqueda ternaria sin acierto",
                    "Reduce al tercio superior hasta probar la ausencia.", "Número de claves ordenadas",
                    ComplexityClass.LOGARITHMIC, "Θ(log n)",
                    AnalysisCase.WORST_CASE, "distinct-keys-target-above-maximum"),
            new AlgorithmDescriptor("array-sum", "Suma de arreglo",
                    "Acumula todos los elementos en un long.", "Longitud del arreglo",
                    ComplexityClass.LINEAR, "Θ(n)",
                    AnalysisCase.FULL_TRAVERSAL, List.of("bounded-uniform-int", "ascending", "descending", "constant"),
                    ImplementationStatus.IMPLEMENTED),
            implemented("linear-search-absent", "Búsqueda lineal sin acierto",
                    "Examina todos los elementos para probar la ausencia.", "Longitud del arreglo",
                    ComplexityClass.LINEAR, "Θ(n)",
                    AnalysisCase.WORST_CASE, "absent-target"),
            implemented("dot-product", "Producto escalar",
                    "Multiplica y suma elementos correspondientes.", "Longitud de cada vector",
                    ComplexityClass.LINEAR, "Θ(n)",
                    AnalysisCase.FULL_TRAVERSAL, "bounded-vector-pair"),
            new AlgorithmDescriptor("merge-sort", "Ordenamiento por mezcla",
                    "Divide y mezcla sin atajos.", "Número de claves",
                    ComplexityClass.LINEARITHMIC, "Θ(n log n)",
                    AnalysisCase.FULL_TRAVERSAL, List.of("bounded-uniform-int", "distinct-key-permutation"),
                    ImplementationStatus.IMPLEMENTED),
            implemented("heap-sort", "Ordenamiento por montículo",
                    "Extrae con descenso hasta hoja y reinserción ascendente.", "Número de claves",
                    ComplexityClass.LINEARITHMIC, "Θ(n log n)",
                    AnalysisCase.WORST_CASE, "distinct-key-permutation"),
            implemented("binary-search-batch", "Lote de búsquedas binarias",
                    "Resuelve consultas ausentes sobre el mismo arreglo.", "Número de claves y de consultas",
                    ComplexityClass.LINEARITHMIC, "Θ(n log n)",
                    AnalysisCase.FULL_TRAVERSAL, "distinct-keys-absent-queries"),
            new AlgorithmDescriptor("insertion-sort-reverse", "Ordenamiento por inserción en orden inverso",
                    "Inserta desplazando las claves previas.", "Número de claves distintas en orden decreciente",
                    ComplexityClass.QUADRATIC, "Θ(n²)",
                    AnalysisCase.WORST_CASE, List.of("strictly-descending-distinct-keys"),
                    ImplementationStatus.IMPLEMENTED),
            implemented("selection-sort", "Ordenamiento por selección",
                    "Examina cada sufijo completo para elegir el mínimo.", "Número de claves",
                    ComplexityClass.QUADRATIC, "Θ(n²)",
                    AnalysisCase.FULL_TRAVERSAL, "distinct-key-permutation"),
            implemented("pair-distance-sum", "Suma de distancias por pares",
                    "Acumula la distancia de cada par i < j.", "Número de valores",
                    ComplexityClass.QUADRATIC, "Θ(n²)",
                    AnalysisCase.FULL_TRAVERSAL, "bounded-int"),
            implemented("dense-matrix-multiply", "Multiplicación densa de matrices",
                    "Calcula todos los productos y sumas de cada celda.", "Lado de cada matriz cuadrada",
                    ComplexityClass.CUBIC, "Θ(n³)",
                    AnalysisCase.FULL_TRAVERSAL, "dense-matrix-pair"),
            implemented("floyd-warshall", "Floyd–Warshall",
                    "Relaja caminos mínimos para todas las ternas k–i–j.", "Número de vértices",
                    ComplexityClass.CUBIC, "Θ(n³)",
                    AnalysisCase.FULL_TRAVERSAL, "dense-nonnegative-weighted-graph"),
            implemented("triangle-count-dense", "Conteo de triángulos por ternas",
                    "Evalúa todas las ternas de vértices.", "Número de vértices del grafo no dirigido",
                    ComplexityClass.CUBIC, "Θ(n³)",
                    AnalysisCase.FULL_TRAVERSAL, "undirected-loopless-graph"),
            implemented("fibonacci-naive", "Fibonacci recursivo",
                    "Evalúa la recurrencia sin memoización.", "Índice del término de Fibonacci",
                    ComplexityClass.EXPONENTIAL, "Θ(φⁿ)",
                    AnalysisCase.FULL_TRAVERSAL, "index-only"),
            implemented("hanoi-traversal", "Recorrido de Torres de Hanói",
                    "Recorre cada movimiento y actualiza un checksum.", "Número de discos",
                    ComplexityClass.EXPONENTIAL, "Θ(2ⁿ)",
                    AnalysisCase.FULL_TRAVERSAL, "standard-three-peg-setup"),
            implemented("subset-enumeration", "Enumeración de subconjuntos",
                    "Explora cada decisión de inclusión y reduce un resumen por hoja.", "Número de valores",
                    ComplexityClass.EXPONENTIAL, "Θ(2ⁿ)",
                    AnalysisCase.FULL_TRAVERSAL, "bounded-int"));

    private static final Map<String, AlgorithmDescriptor> BY_ID = ENTRIES.stream()
            .collect(Collectors.toUnmodifiableMap(AlgorithmDescriptor::id, Function.identity()));

    private AlgorithmCatalog() {
    }

    public static List<AlgorithmDescriptor> all() {
        return ENTRIES;
    }

    public static Optional<AlgorithmDescriptor> findById(String id) {
        return Optional.ofNullable(BY_ID.get(id));
    }

    private static AlgorithmDescriptor implemented(
            String id, String name, String description, String inputSizeDefinition,
            ComplexityClass complexityClass, String timeComplexity, AnalysisCase analysisCase,
            String inputDistribution) {
        return new AlgorithmDescriptor(id, name, description, inputSizeDefinition,
                complexityClass, timeComplexity, analysisCase, List.of(inputDistribution),
                ImplementationStatus.IMPLEMENTED);
    }

    private static AlgorithmDescriptor proposed(
            String id, String name, String description, String inputSizeDefinition,
            ComplexityClass complexityClass, String timeComplexity, AnalysisCase analysisCase,
            String... inputDistributions) {
        return new AlgorithmDescriptor(id, name, description, inputSizeDefinition,
                complexityClass, timeComplexity, analysisCase, List.of(inputDistributions),
                ImplementationStatus.PROPOSED);
    }
}
