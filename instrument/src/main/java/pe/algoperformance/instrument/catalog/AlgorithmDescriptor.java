package pe.algoperformance.instrument.catalog;

import java.util.List;
import java.util.Objects;

/** Metadatos científicos de una variante, independientes de JMH. */
public record AlgorithmDescriptor(
        String id,
        String name,
        String description,
        String inputSizeDefinition,
        ComplexityClass complexityClass,
        String timeComplexity,
        AnalysisCase analysisCase,
        List<String> inputDistributions,
        ImplementationStatus status) {

    public AlgorithmDescriptor {
        Objects.requireNonNull(id, "id");
        if (!id.matches("[a-z][a-z0-9]*(?:-[a-z0-9]+)*")) {
            throw new IllegalArgumentException("Identificador de algoritmo inválido: " + id);
        }
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(description, "description");
        Objects.requireNonNull(inputSizeDefinition, "inputSizeDefinition");
        Objects.requireNonNull(complexityClass, "complexityClass");
        Objects.requireNonNull(timeComplexity, "timeComplexity");
        Objects.requireNonNull(analysisCase, "analysisCase");
        inputDistributions = List.copyOf(inputDistributions);
        if (inputDistributions.isEmpty()) {
            throw new IllegalArgumentException("Se requiere al menos un perfil de entrada.");
        }
        Objects.requireNonNull(status, "status");
    }
}
