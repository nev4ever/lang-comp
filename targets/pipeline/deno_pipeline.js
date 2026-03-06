function sqliteQuery(dbPath, sql) {
  const cmd = new Deno.Command("sqlite3", { args: [dbPath, sql], stdout: "piped", stderr: "piped" });
  const out = cmd.outputSync();
  if (out.code !== 0) {
    throw new Error(new TextDecoder().decode(out.stderr) || "sqlite3 failed");
  }
  return new TextDecoder().decode(out.stdout).trim();
}

function initDb(dbPath) {
  sqliteQuery(dbPath, "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, total_cents INTEGER NOT NULL);");
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) out[argv[i]] = argv[i + 1];
  return out;
}

async function runStd(port, dbPath) {
  initDb(dbPath);
  Deno.serve({ hostname: "127.0.0.1", port }, async (req) => {
    const url = new URL(req.url);
    if (req.method === "GET" && url.pathname === "/health") {
      return new Response('{"ok":true}', { headers: { "content-type": "application/json" } });
    }
    if (req.method === "POST" && url.pathname === "/orders") {
      try {
        const payload = await req.json();
        const customerId = Number.parseInt(payload.customerId || 0, 10);
        const itemCount = Number.parseInt(payload.itemCount || 0, 10);
        const baseCents = Number.parseInt(payload.baseCents || 0, 10);
        const totalCents = baseCents * itemCount + (customerId % 7);
        const out = sqliteQuery(
          dbPath,
          `BEGIN; INSERT INTO orders(customer_id,total_cents) VALUES(${customerId},${totalCents}); SELECT last_insert_rowid(); COMMIT;`,
        );
        const m = out.match(/(\d+)\s*$/);
        const orderId = m ? Number.parseInt(m[1], 10) : 0;
        const stored = Number.parseInt(sqliteQuery(dbPath, `SELECT total_cents FROM orders WHERE id=${orderId};`) || "0", 10);
        return Response.json({ ok: true, orderId, totalCents: stored });
      } catch (err) {
        return Response.json({ ok: false, error: String(err) }, { status: 500 });
      }
    }
    return new Response("Not found", { status: 404 });
  });
}

async function runOak(port, dbPath) {
  let Application;
  let Router;
  try {
    ({ Application, Router } = await import("jsr:@oak/oak"));
  } catch {
    console.error("SKIP: oak not installed or unavailable");
    Deno.exit(3);
  }
  initDb(dbPath);
  const app = new Application();
  const router = new Router();
  router.get("/health", (ctx) => { ctx.response.body = { ok: true }; });
  router.post("/orders", async (ctx) => {
    try {
      const payload = await ctx.request.body.json();
      const customerId = Number.parseInt(payload.customerId || 0, 10);
      const itemCount = Number.parseInt(payload.itemCount || 0, 10);
      const baseCents = Number.parseInt(payload.baseCents || 0, 10);
      const totalCents = baseCents * itemCount + (customerId % 7);
      const out = sqliteQuery(
        dbPath,
        `BEGIN; INSERT INTO orders(customer_id,total_cents) VALUES(${customerId},${totalCents}); SELECT last_insert_rowid(); COMMIT;`,
      );
      const m = out.match(/(\d+)\s*$/);
      const orderId = m ? Number.parseInt(m[1], 10) : 0;
      const stored = Number.parseInt(sqliteQuery(dbPath, `SELECT total_cents FROM orders WHERE id=${orderId};`) || "0", 10);
      ctx.response.body = { ok: true, orderId, totalCents: stored };
    } catch (err) {
      ctx.response.status = 500;
      ctx.response.body = { ok: false, error: String(err) };
    }
  });
  app.use(router.routes());
  app.use(router.allowedMethods());
  await app.listen({ hostname: "127.0.0.1", port });
}

if (import.meta.main) {
  const args = parseArgs(Deno.args);
  const port = Number.parseInt(args["--port"] || "0", 10);
  const db = args["--db"];
  const mode = args["--mode"] || "std";
  if (!port || !db) {
    console.error("Usage: deno_pipeline.js --port <n> --db <path> --mode <std|oak>");
    Deno.exit(1);
  }
  if (mode === "oak") await runOak(port, db);
  else await runStd(port, db);
}
