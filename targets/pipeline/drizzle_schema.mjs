import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import { integer, pgTable, serial, varchar } from "drizzle-orm/pg-core";
import pg from "pg";

const { Pool } = pg;

export const customers = pgTable("customers", {
  id: integer("id").primaryKey(),
  name: varchar("name", { length: 120 }).notNull(),
  tier: integer("tier").notNull().default(0),
});

export const orders = pgTable("orders", {
  id: serial("id").primaryKey(),
  customerId: integer("customer_id")
    .notNull()
    .references(() => customers.id),
  itemCount: integer("item_count").notNull(),
  totalCents: integer("total_cents").notNull(),
});

export async function createDrizzlePostgres(dbUrl) {
  const pool = new Pool({ connectionString: dbUrl });
  const db = drizzle(pool);

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

  return { pool, db };
}

export async function upsertCustomerDrizzle(db, customerId) {
  await db
    .insert(customers)
    .values({
      id: customerId,
      name: `Customer ${customerId}`,
      tier: customerId % 3,
    })
    .onConflictDoUpdate({
      target: customers.id,
      set: { name: `Customer ${customerId}`, tier: customerId % 3 },
    });
}

export async function insertOrderDrizzle(db, payload) {
  const rows = await db
    .insert(orders)
    .values({
      customerId: payload.customerId,
      itemCount: payload.itemCount,
      totalCents: payload.totalCents,
    })
    .returning({ id: orders.id });
  return rows[0]?.id ?? 0;
}

export async function fetchOrderJoinDrizzle(db, orderId) {
  const rows = await db
    .select({
      orderId: orders.id,
      totalCents: orders.totalCents,
      customerId: customers.id,
      customerTier: customers.tier,
    })
    .from(orders)
    .innerJoin(customers, eq(orders.customerId, customers.id))
    .where(eq(orders.id, orderId))
    .limit(1);
  return rows[0] ?? null;
}

