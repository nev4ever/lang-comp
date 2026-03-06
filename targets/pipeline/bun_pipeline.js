#!/usr/bin/env bun
import { spawnSync } from "bun";
import pg from "pg";
import {
  createDrizzlePostgres,
  fetchOrderJoinDrizzle,
  insertOrderDrizzle,
  upsertCustomerDrizzle,
} from "./drizzle_schema.mjs";

const { Pool } = pg;

function sqliteQuery(dbPath, sql) {
  const p = spawnSync(["sqlite3", dbPath, sql], { stdout: "pipe", stderr: "pipe" });
  if (p.exitCode !== 0) {
    throw new Error(new TextDecoder().decode(p.stderr) || "sqlite3 failed");
  }
  return new TextDecoder().decode(p.stdout).trim();
}

function initDbSqlite(dbPath) {
  sqliteQuery(dbPath, "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, tier INTEGER NOT NULL DEFAULT 0);");
  sqliteQuery(dbPath, "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, item_count INTEGER NOT NULL, total_cents INTEGER NOT NULL);");
}

async function createPgSql(dbUrl) {
  const pool = new Pool({ connectionString: dbUrl, max: 20 });
  await pool.query(`
    CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY,
      name VARCHAR(120) NOT NULL,
      tier INTEGER NOT NULL DEFAULT 0
    );
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS orders (
      id SERIAL PRIMARY KEY,
      customer_id INTEGER NOT NULL REFERENCES customers(id),
      item_count INTEGER NOT NULL,
      total_cents INTEGER NOT NULL
    );
  `);
  return pool;
}

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i += 2) out[argv[i]] = argv[i + 1];
  return out;
}

async function createSqlStore(dbBackend, dbPath, pgUrl) {
  if (dbBackend === "postgres") {
    if (!pgUrl) throw new Error("missing --pg-url / PIPELINE_PG_URL");
    const pool = await createPgSql(pgUrl);
    return {
      close: async () => pool.end(),
      handle: async ({ customerId, itemCount, totalCents }) => {
        await pool.query(
          `INSERT INTO customers(id, name, tier)
           VALUES ($1, $2, $3)
           ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, tier = EXCLUDED.tier`,
          [customerId, `Customer ${customerId}`, customerId % 3],
        );
        const ins = await pool.query(
          "INSERT INTO orders(customer_id, item_count, total_cents) VALUES ($1, $2, $3) RETURNING id",
          [customerId, itemCount, totalCents],
        );
        const orderId = Number.parseInt(ins.rows[0]?.id ?? 0, 10);
        const joined = await pool.query(
          `SELECT o.total_cents AS total_cents
             FROM orders o
             INNER JOIN customers c ON c.id = o.customer_id
            WHERE o.id = $1
            LIMIT 1`,
          [orderId],
        );
        const stored = Number.parseInt(joined.rows[0]?.total_cents ?? 0, 10);
        return { orderId, totalCents: stored };
      },
    };
  }

  initDbSqlite(dbPath);
  return {
    close: async () => {},
    handle: async ({ customerId, itemCount, totalCents }) => {
      sqliteQuery(dbPath, `INSERT OR REPLACE INTO customers(id,name,tier) VALUES(${customerId},'Customer ${customerId}',${customerId % 3});`);
      const out = sqliteQuery(
        dbPath,
        `BEGIN; INSERT INTO orders(customer_id,item_count,total_cents) VALUES(${customerId},${itemCount},${totalCents}); SELECT last_insert_rowid(); COMMIT;`,
      );
      const m = out.match(/(\d+)\s*$/);
      const orderId = m ? Number.parseInt(m[1], 10) : 0;
      const stored = Number.parseInt(
        sqliteQuery(dbPath, `SELECT o.total_cents FROM orders o INNER JOIN customers c ON c.id = o.customer_id WHERE o.id=${orderId} LIMIT 1;`) || "0",
        10,
      );
      return { orderId, totalCents: stored };
    },
  };
}

const args = parseArgs(process.argv);
const port = Number.parseInt(args["--port"] || "0", 10);
const dbPath = args["--db"];
const mode = args["--mode"] || "builtin-sql";
const dbBackend = args["--db-backend"] || "sqlite";
const pgUrl = args["--pg-url"] || process.env.PIPELINE_PG_URL || "";
if (!port || !dbPath) {
  console.error("Usage: bun_pipeline.js --port <n> --db <path> --mode <builtin-sql|builtin-drizzle> [--db-backend sqlite|postgres] [--pg-url <dsn>]");
  process.exit(1);
}

let store = null;
let drizzle = null;

if (mode === "builtin-drizzle") {
  if (dbBackend !== "postgres" || !pgUrl) {
    console.error("SKIP: bun drizzle mode requires --db-backend postgres and --pg-url");
    process.exit(3);
  }
  drizzle = await createDrizzlePostgres(pgUrl);
} else {
  store = await createSqlStore(dbBackend, dbPath, pgUrl);
}

const server = Bun.serve({
  hostname: "127.0.0.1",
  port,
  async fetch(req) {
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

        let orderId = 0;
        let stored = 0;

        if (mode === "builtin-drizzle") {
          await upsertCustomerDrizzle(drizzle.db, customerId);
          orderId = await insertOrderDrizzle(drizzle.db, { customerId, itemCount, totalCents });
          const row = await fetchOrderJoinDrizzle(drizzle.db, orderId);
          stored = Number.parseInt(row?.totalCents ?? 0, 10);
        } else {
          const out = await store.handle({ customerId, itemCount, totalCents });
          orderId = out.orderId;
          stored = out.totalCents;
        }

        return Response.json({ ok: true, orderId, totalCents: stored });
      } catch (err) {
        return Response.json({ ok: false, error: String(err) }, { status: 500 });
      }
    }
    return new Response("Not Found", { status: 404 });
  },
});

const cleanup = async () => {
  try {
    if (store) await store.close();
    if (drizzle?.pool) await drizzle.pool.end();
  } finally {
    server.stop(true);
    process.exit(0);
  }
};
process.on("SIGTERM", cleanup);
process.on("SIGINT", cleanup);
