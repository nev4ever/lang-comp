import { DataTypes, QueryTypes, Sequelize } from "sequelize";

export async function createSequelizePostgres(dbUrl) {
  const sequelize = new Sequelize(dbUrl, {
    dialect: "postgres",
    logging: false,
    pool: { max: 20, min: 0, idle: 10_000 },
  });

  const Customer = sequelize.define(
    "Customer",
    {
      id: { type: DataTypes.INTEGER, primaryKey: true },
      name: { type: DataTypes.STRING(120), allowNull: false },
      tier: { type: DataTypes.INTEGER, allowNull: false, defaultValue: 0 },
    },
    { tableName: "customers", timestamps: false },
  );

  const Order = sequelize.define(
    "Order",
    {
      id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
      customerId: { type: DataTypes.INTEGER, allowNull: false, field: "customer_id" },
      itemCount: { type: DataTypes.INTEGER, allowNull: false, field: "item_count" },
      totalCents: { type: DataTypes.INTEGER, allowNull: false, field: "total_cents" },
    },
    { tableName: "orders", timestamps: false },
  );

  Customer.hasMany(Order, { foreignKey: "customerId" });
  Order.belongsTo(Customer, { foreignKey: "customerId" });

  await sequelize.authenticate();
  await sequelize.sync();

  return { sequelize, Customer, Order };
}

export async function upsertCustomerSequelize(Customer, customerId) {
  await Customer.upsert({
    id: customerId,
    name: `Customer ${customerId}`,
    tier: customerId % 3,
  });
}

export async function insertOrderSequelize(Order, payload) {
  const row = await Order.create({
    customerId: payload.customerId,
    itemCount: payload.itemCount,
    totalCents: payload.totalCents,
  });
  return row.id;
}

export async function fetchOrderJoinSequelize(sequelize, orderId) {
  const rows = await sequelize.query(
    `
      SELECT
        o.id AS "orderId",
        o.total_cents AS "totalCents",
        c.id AS "customerId",
        c.tier AS "customerTier"
      FROM orders o
      INNER JOIN customers c ON c.id = o.customer_id
      WHERE o.id = :orderId
      LIMIT 1
    `,
    { replacements: { orderId }, type: QueryTypes.SELECT },
  );
  return rows[0] ?? null;
}

