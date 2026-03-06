import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class PipelineServer {
    private static final Pattern CUSTOMER_RE = Pattern.compile("\"customerId\"\\s*:\\s*(\\d+)");
    private static final Pattern ITEM_RE = Pattern.compile("\"itemCount\"\\s*:\\s*(\\d+)");
    private static final Pattern BASE_RE = Pattern.compile("\"baseCents\"\\s*:\\s*(\\d+)");
    private static final Pattern DIGIT_RE = Pattern.compile("(\\d+)");

    private static String dbPath;

    private static String sqliteQuery(String sql) throws Exception {
        Process p = new ProcessBuilder("sqlite3", dbPath, sql).start();
        byte[] out = p.getInputStream().readAllBytes();
        byte[] err = p.getErrorStream().readAllBytes();
        int code = p.waitFor();
        if (code != 0) {
            throw new RuntimeException(new String(err, StandardCharsets.UTF_8));
        }
        return new String(out, StandardCharsets.UTF_8).trim();
    }

    private static int extractInt(Pattern p, String text) {
        Matcher m = p.matcher(text);
        if (m.find()) return Integer.parseInt(m.group(1));
        return 0;
    }

    private static void writeJson(HttpExchange ex, int code, String body) throws IOException {
        byte[] b = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json");
        ex.sendResponseHeaders(code, b.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(b);
        }
    }

    public static void main(String[] args) throws Exception {
        int port = 0;
        dbPath = "";
        for (int i = 0; i + 1 < args.length; i += 2) {
            if (args[i].equals("--port")) port = Integer.parseInt(args[i + 1]);
            if (args[i].equals("--db")) dbPath = args[i + 1];
        }
        if (port == 0 || dbPath.isEmpty()) {
            System.err.println("Usage: PipelineServer --port <n> --db <path>");
            System.exit(1);
        }

        sqliteQuery("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, total_cents INTEGER NOT NULL);");

        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0);
        server.createContext("/health", ex -> writeJson(ex, 200, "{\"ok\":true}"));
        server.createContext("/orders", ex -> {
            if (!"POST".equals(ex.getRequestMethod())) {
                ex.sendResponseHeaders(404, -1);
                return;
            }
            try {
                InputStream is = ex.getRequestBody();
                String body = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                int customerId = extractInt(CUSTOMER_RE, body);
                int itemCount = extractInt(ITEM_RE, body);
                int baseCents = extractInt(BASE_RE, body);
                int totalCents = baseCents * itemCount + (customerId % 7);

                String out = sqliteQuery("BEGIN; INSERT INTO orders(customer_id,total_cents) VALUES(" + customerId + "," + totalCents + "); SELECT last_insert_rowid(); COMMIT;");
                Matcher m = DIGIT_RE.matcher(out);
                int orderId = 0;
                while (m.find()) orderId = Integer.parseInt(m.group(1));

                String storedRaw = sqliteQuery("SELECT total_cents FROM orders WHERE id=" + orderId + ";");
                int stored = storedRaw.isEmpty() ? 0 : Integer.parseInt(storedRaw);
                writeJson(ex, 200, "{\"ok\":true,\"orderId\":" + orderId + ",\"totalCents\":" + stored + "}");
            } catch (Exception err) {
                writeJson(ex, 500, "{\"ok\":false,\"error\":\"" + err.getMessage().replace("\"", "") + "\"}");
            }
        });

        server.start();
    }
}
