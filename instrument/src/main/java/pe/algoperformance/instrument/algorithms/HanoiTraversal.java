package pe.algoperformance.instrument.algorithms;

/** Tres pilas planas. El resumen pondera cada disco según origen y destino. */
public final class HanoiTraversal {
    private final int disks;
    private final int[] towers;
    private final int[] heights = new int[3];

    public HanoiTraversal(int disks) {
        ExponentialOperations.requireSize(disks, ExponentialOperations.MAX_BINARY_RECURSION);
        this.disks = disks;
        towers = new int[3 * disks];
        restore();
    }

    public void restore() {
        heights[0] = disks;
        heights[1] = 0;
        heights[2] = 0;
        for (int level = 0; level < disks; level++) {
            towers[level] = disks - level;
        }
    }

    /** Requiere el estado inicial restaurado. */
    public long solve() {
        return transfer(disks, 0, 2, 1);
    }

    private long transfer(int n, int from, int to, int spare) {
        if (n == 0) {
            return 0;
        }
        long before = transfer(n - 1, from, spare, to);
        long moved = move(from, to);
        return before + moved + transfer(n - 1, spare, to, from);
    }

    private long move(int from, int to) {
        int disk = towers[from * disks + --heights[from]];
        towers[to * disks + heights[to]++] = disk;
        return (long) disk * (1 + 3 * from + to);
    }
}
