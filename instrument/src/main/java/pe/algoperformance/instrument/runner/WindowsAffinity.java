package pe.algoperformance.instrument.runner;

import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.foreign.ValueLayout;
import java.nio.file.Files;
import java.nio.file.Path;

/** Comprueba en la JVM hija la máscara establecida por el lanzador de Windows. */
public final class WindowsAffinity {
    public static final String EXPECTED_MASK = "ALGOPERFORMANCE_EXPECTED_AFFINITY";

    private WindowsAffinity() {
    }

    public static void verify() {
        String expected = System.getenv(EXPECTED_MASK);
        if (expected == null) {
            return;
        }
        try (var arena = Arena.ofConfined()) {
            var kernel = SymbolLookup.libraryLookup("kernel32.dll", arena);
            var linker = Linker.nativeLinker();
            var current = linker.downcallHandle(kernel.find("GetCurrentProcess").orElseThrow(),
                    FunctionDescriptor.of(ValueLayout.ADDRESS));
            var affinity = linker.downcallHandle(kernel.find("GetProcessAffinityMask").orElseThrow(),
                    FunctionDescriptor.of(ValueLayout.JAVA_INT, ValueLayout.ADDRESS,
                            ValueLayout.ADDRESS, ValueLayout.ADDRESS));
            var process = arena.allocate(ValueLayout.JAVA_LONG);
            var system = arena.allocate(ValueLayout.JAVA_LONG);
            var handle = (MemorySegment) current.invokeExact();
            if (ValueLayout.ADDRESS.byteSize() != Long.BYTES
                    || (int) affinity.invokeExact(handle, process, system) == 0) {
                throw new IllegalStateException("GetProcessAffinityMask falló.");
            }
            long actual = process.get(ValueLayout.JAVA_LONG, 0);
            if (actual != Long.parseUnsignedLong(expected, 16)) {
                throw new IllegalStateException("Máscara esperada " + expected + ", efectiva "
                        + Long.toHexString(actual));
            }
            long pid = ProcessHandle.current().pid();
            String evidence = "Affinity verified before warmup: pid=%d mask=0x%s%n"
                    .formatted(pid, Long.toHexString(actual));
            String destination = System.getProperty("algoperformance.affinity.evidence");
            if (destination != null) {
                Files.writeString(Path.of(destination).resolve("affinity-" + pid + ".txt"), evidence);
            }
            System.out.print(evidence);
        } catch (RuntimeException | Error failure) {
            throw failure;
        } catch (Throwable failure) {
            throw new IllegalStateException("Verificación de afinidad del fork fallida.", failure);
        }
    }

    public static void main(String[] args) {
        if (System.getenv(EXPECTED_MASK) == null) {
            throw new IllegalStateException("Falta la máscara esperada.");
        }
        verify();
    }
}
