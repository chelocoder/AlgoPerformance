package pe.algoperformance.direct;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

final class Fingerprint {
    static String sha256(Object... inputs) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            for (Object input : inputs) {
                switch (input) {
                    case int[] values -> {
                        append(digest, 1, 1);
                        append(digest, values.length, 4);
                        for (int value : values) append(digest, value, 4);
                    }
                    case long[] values -> {
                        append(digest, 2, 1);
                        append(digest, values.length, 4);
                        for (long value : values) append(digest, value, 8);
                    }
                    case byte[] values -> {
                        append(digest, 3, 1);
                        append(digest, values.length, 4);
                        digest.update(values);
                    }
                    case Integer value -> {
                        append(digest, 4, 1);
                        append(digest, value, 4);
                    }
                    case Long value -> {
                        append(digest, 5, 1);
                        append(digest, value, 8);
                    }
                    default -> throw new IllegalArgumentException("Tipo de entrada no admitido");
                }
            }
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException unexpected) {
            throw new AssertionError(unexpected);
        }
    }

    private static void append(MessageDigest digest, long value, int bytes) {
        for (int offset = 0; offset < bytes * 8; offset += 8) {
            digest.update((byte) (value >>> offset));
        }
    }

    static long output(int[] values) {
        long checksum = 1;
        for (int value : values) checksum = mix(checksum, value);
        return checksum;
    }

    static long output(long[] values) {
        long checksum = 1;
        for (long value : values) checksum = mix(checksum, value);
        return checksum;
    }

    static long mix(long previous, long value) {
        return previous * 31 + value;
    }
}
