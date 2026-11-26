package pe.algoperformance.instrument.algorithms;

/** Cola FIFO de capacidad fija. Todas las posiciones son utilizables. */
public final class IntRingBuffer {
    private final int[] values;
    private int head;
    private int tail;
    private int size;

    public IntRingBuffer(int capacity) {
        if (capacity < 2) {
            throw new IllegalArgumentException("La capacidad debe ser al menos dos.");
        }
        values = new int[capacity];
    }

    /** Inserta y devuelve la ocupación resultante. */
    public int enqueue(int value) {
        if (size == values.length) {
            throw new IllegalStateException("Cola llena.");
        }
        values[tail] = value;
        tail = advance(tail);
        return ++size;
    }

    public int dequeue() {
        if (size == 0) {
            throw new IllegalStateException("Cola vacía.");
        }
        int value = values[head];
        head = advance(head);
        size--;
        return value;
    }

    private int advance(int index) {
        int next = index + 1;
        return next == values.length ? 0 : next;
    }
}
