package pe.algoperformance.direct;

import pe.algoperformance.instrument.catalog.AlgorithmCatalog;

record Settings(String algorithm, int size, long seed, int minimum, int maximum, Mode mode,
                int warmups, int measurements, int operations, int windowMs) {
    static final long BUDGET = 128L << 20;
    enum Mode { COLD, SINGLE, BATCH }

    Settings {
        if (AlgorithmCatalog.findById(algorithm).isEmpty() && !Fixtures.isControl(algorithm)) {
            throw new IllegalArgumentException("Algoritmo o control desconocido");
        }
        if (size < 0 || size > Fixtures.pilotCeiling(algorithm) || minimum > maximum
                || warmups < 0 || warmups > 10000
                || measurements < 1 || measurements > 1000 || operations < 1
                || operations > 1048576 || windowMs < 0 || windowMs > 1000) {
            throw new IllegalArgumentException("Parámetros fuera de rango");
        }
        if (mode == Mode.COLD && (warmups != 0 || measurements != 1)
                || mode != Mode.BATCH && (operations != 1 || windowMs != 0)
                || mode == Mode.BATCH && Fixtures.singleOnly(algorithm)
                || windowMs != 0 && operations != 1
                || algorithm.equals("control-clock") && mode != Mode.SINGLE
                || isBatchControl(algorithm) && (mode != Mode.BATCH || windowMs != 0)) {
            throw new IllegalArgumentException("Protocolo incompatible con el estado o el lote");
        }
        long bytes = Fixtures.payload(algorithm, size);
        if (bytes > BUDGET - 16L * operations) {
            throw new IllegalArgumentException("Carga útil superior a 128 MiB");
        }
    }

    private static boolean isBatchControl(String algorithm) {
        return algorithm.equals("control-loop") || algorithm.equals("control-consume");
    }

    static Settings parse(String[] args, int offset) {
        if (args.length != offset + 10) {
            throw new IllegalArgumentException("Se esperan diez parámetros del tratamiento");
        }
        return new Settings(args[offset], Integer.parseInt(args[offset + 1]),
                Long.parseLong(args[offset + 2]), Integer.parseInt(args[offset + 3]),
                Integer.parseInt(args[offset + 4]), Mode.valueOf(args[offset + 5]),
                Integer.parseInt(args[offset + 6]), Integer.parseInt(args[offset + 7]),
                Integer.parseInt(args[offset + 8]), Integer.parseInt(args[offset + 9]));
    }
}


