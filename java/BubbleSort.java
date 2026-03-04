import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class BubbleSort {
    private static void bubbleSort(int[] values) {
        int n = values.length;
        for (int i = 0; i < n; i++) {
            boolean swapped = false;
            for (int j = 0; j < n - i - 1; j++) {
                if (values[j] > values[j + 1]) {
                    int tmp = values[j];
                    values[j] = values[j + 1];
                    values[j + 1] = tmp;
                    swapped = true;
                }
            }
            if (!swapped) {
                break;
            }
        }
    }

    private static long checksum(int[] values) {
        long sum = 0;
        for (int value : values) {
            sum += value;
        }
        return sum;
    }

    private static int[] readNumbers(String file) throws IOException {
        List<String> lines = Files.readAllLines(Path.of(file));
        List<Integer> values = new ArrayList<>();
        for (String line : lines) {
            String trimmed = line.trim();
            if (!trimmed.isEmpty()) {
                values.add(Integer.parseInt(trimmed));
            }
        }
        int[] result = new int[values.size()];
        for (int i = 0; i < values.size(); i++) {
            result[i] = values.get(i);
        }
        return result;
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: BubbleSort <numbers_file>");
            System.exit(1);
        }

        int[] values = readNumbers(args[0]);
        long start = System.nanoTime();
        bubbleSort(values);
        double elapsedMs = (System.nanoTime() - start) / 1_000_000.0;

        System.out.printf("LANG=java N=%d ELAPSED_MS=%.3f CHECKSUM=%d%n", values.length, elapsedMs, checksum(values));
    }
}
