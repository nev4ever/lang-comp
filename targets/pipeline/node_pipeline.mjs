#!/usr/bin/env node
import http from "node:http";
import { spawnSync } from "node:child_process";
import pg from "pg";
import {
  createDrizzlePostgres,
  fetchOrderJoinDrizzle,
  insertOrderDrizzle,
  upsertCustomerDrizzle,
} from "./drizzle_schema.mjs";
import {
  createSequelizePostgres,
  fetchOrderJoinSequelize,
  insertOrderSequelize,
  upsertCustomerSequelize,
} from "./sequelize_models.mjs";

const { Pool } = pg;

function sqliteQuery(dbPath, sql) {
  const proc = spawnSync("sqlite3", [dbPath, sql], { encoding: "utf-8" });
  if (proc.status !== 0) {
    throw new Error(proc.stderr || "sqlite3 failed");
  }
  return (proc.stdout || "").trim();
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
      sqliteQuery(
        dbPath,
        `INSERT OR REPLACE INTO customers(id,name,tier) VALUES(${customerId},'Customer ${customerId}',${customerId % 3});`,
      );
      const out = sqliteQuery(
        dbPath,
        `BEGIN; INSERT INTO orders(customer_id,item_count,total_cents) VALUES(${customerId},${itemCount},${totalCents}); SELECT last_insert_rowid(); COMMIT;`,
      );
      const m = out.match(/(\d+)\s*$/);
      const orderId = m ? Number.parseInt(m[1], 10) : 0;
      const stored = Number.parseInt(
        sqliteQuery(
          dbPath,
          `SELECT o.total_cents FROM orders o INNER JOIN customers c ON c.id = o.customer_id WHERE o.id=${orderId} LIMIT 1;`,
        ) || "0",
        10,
      );
      return { orderId, totalCents: stored };
    },
  };
}

async function runPlain(port, dbPath, dbBackend, pgUrl) {
  const store = await createSqlStore(dbBackend, dbPath, pgUrl);
  const server = http.createServer((req, res) => {
    if (req.method === "GET" && req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end('{"ok":true}');
      return;
    }
    if (req.method === "POST" && req.url === "/orders") {
      const chunks = [];
      req.on("data", (c) => chunks.push(c));
      req.on("end", async () => {
        try {
          const payload = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
          const customerId = Number.parseInt(payload.customerId || 0, 10);
          const itemCount = Number.parseInt(payload.itemCount || 0, 10);
          const baseCents = Number.parseInt(payload.baseCents || 0, 10);
          const totalCents = baseCents * itemCount + (customerId % 7);
          const out = await store.handle({ customerId, itemCount, totalCents });
          const body = JSON.stringify({ ok: true, orderId: out.orderId, totalCents: out.totalCents });
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(body);
        } catch (err) {
          res.writeHead(500, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ ok: false, error: String(err) }));
        }
      });
      return;
    }
    res.writeHead(404);
    res.end();
  });
  server.listen(port, "127.0.0.1");

  const cleanup = async () => {
    try {
      await store.close();
    } finally {
      server.close(() => process.exit(0));
    }
  };
  process.on("SIGTERM", cleanup);
  process.on("SIGINT", cleanup);
}

async function runExpress(port, dbPath, ormMode, dbBackend, pgUrl) {
  let express;
  try {
    ({ default: express } = await import("express"));
  } catch {
    console.error("SKIP: express not installed");
    process.exit(3);
  }

  let orm = null;
  let sqlStore = null;

  if (ormMode === "sequelize") {
    try {
      await import("sequelize");
      await import("pg");
    } catch {
      console.error("SKIP: sequelize/pg not installed");
      process.exit(3);
    }
    if (dbBackend !== "postgres" || !pgUrl) {
      console.error("SKIP: sequelize mode requires --db-backend postgres and --pg-url");
      process.exit(3);
    }
    orm = await createSequelizePostgres(pgUrl);
  } else if (ormMode === "drizzle") {
    try {
      await import("drizzle-orm");
      await import("pg");
    } catch {
      console.error("SKIP: drizzle or pg not installed");
      process.exit(3);
    }
    if (dbBackend !== "postgres" || !pgUrl) {
      console.error("SKIP: drizzle mode requires --db-backend postgres and --pg-url");
      process.exit(3);
    }
    orm = await createDrizzlePostgres(pgUrl);
  } else {
    sqlStore = await createSqlStore(dbBackend, dbPath, pgUrl);
  }

  const app = express();
  app.use(express.json());
  app.get("/health", (_req, res) => res.json({ ok: true }));
  app.post("/orders", async (req, res) => {
    try {
      const customerId = Number.parseInt(req.body.customerId || 0, 10);
      const itemCount = Number.parseInt(req.body.itemCount || 0, 10);
      const baseCents = Number.parseInt(req.body.baseCents || 0, 10);
      const totalCents = baseCents * itemCount + (customerId % 7);
      const payload = { customerId, itemCount, totalCents };

      let orderId = 0;
      let stored = 0;

      if (ormMode === "sequelize") {
        await upsertCustomerSequelize(orm.Customer, customerId);
        orderId = await insertOrderSequelize(orm.Order, payload);
        const row = await fetchOrderJoinSequelize(orm.sequelize, orderId);
        stored = Number.parseInt(row?.totalCents ?? 0, 10);
      } else if (ormMode === "drizzle") {
        await upsertCustomerDrizzle(orm.db, customerId);
        orderId = await insertOrderDrizzle(orm.db, payload);
        const row = await fetchOrderJoinDrizzle(orm.db, orderId);
        stored = Number.parseInt(row?.totalCents ?? 0, 10);
      } else {
        const out = await sqlStore.handle(payload);
        orderId = out.orderId;
        stored = out.totalCents;
      }

      res.json({ ok: true, orderId, totalCents: stored });
    } catch (err) {
      res.status(500).json({ ok: false, error: String(err) });
    }
  });

  const server = app.listen(port, "127.0.0.1");
  const cleanup = async () => {
    try {
      if (ormMode === "sequelize" && orm?.sequelize) await orm.sequelize.close();
      if (ormMode === "drizzle" && orm?.pool) await orm.pool.end();
      if (ormMode === "plain" && sqlStore) await sqlStore.close();
    } catch {
      // ignore cleanup failures during shutdown
    } finally {
      server.close(() => process.exit(0));
    }
  };
  process.on("SIGTERM", cleanup);
  process.on("SIGINT", cleanup);
}

async function main() {
  const args = parseArgs(process.argv);
  const port = Number.parseInt(args["--port"] || "0", 10);
  const db = args["--db"];
  const mode = args["--mode"] || "plain";
  const dbBackend = args["--db-backend"] || "sqlite";
  const pgUrl = args["--pg-url"] || process.env.PIPELINE_PG_URL || "";
  if (!port || !db) {
    console.error("Usage: node_pipeline.mjs --port <n> --db <path> --mode <plain|express-sql|express-sequelize|express-drizzle> [--db-backend sqlite|postgres] [--pg-url <dsn>]");
    process.exit(1);
  }

  if (mode === "plain") {
    await runPlain(port, db, dbBackend, pgUrl);
  } else if (mode === "express-sql") {
    await runExpress(port, db, "plain", dbBackend, pgUrl);
  } else if (mode === "express-sequelize") {
    await runExpress(port, db, "sequelize", dbBackend, pgUrl);
  } else if (mode === "express-drizzle") {
    await runExpress(port, db, "drizzle", dbBackend, pgUrl);
  } else {
    console.error(`unknown mode: ${mode}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
