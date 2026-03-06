#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except Exception:
    print("SKIP: fastapi/uvicorn not installed", file=sys.stderr)
    raise SystemExit(3)


def sqlite_query(db_path: str, sql: str) -> str:
    proc = subprocess.run(["sqlite3", db_path, sql], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "sqlite3 failed")
    return proc.stdout.strip()


def init_db(db_path: str) -> None:
    sqlite_query(
        db_path,
        "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, total_cents INTEGER NOT NULL);",
    )


class OrderIn(BaseModel):
    customerId: int
    itemCount: int
    baseCents: int


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()

    init_db(args.db)
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/orders")
    def orders(payload: OrderIn) -> dict[str, int | bool]:
        customer_id = int(payload.customerId)
        item_count = int(payload.itemCount)
        base_cents = int(payload.baseCents)
        total_cents = base_cents * item_count + (customer_id % 7)
        try:
            out = sqlite_query(
                args.db,
                f"BEGIN; INSERT INTO orders(customer_id,total_cents) VALUES({customer_id},{total_cents}); SELECT last_insert_rowid(); COMMIT;",
            )
            m = re.findall(r"\d+", out)
            order_id = int(m[-1]) if m else 0
            row = sqlite_query(args.db, f"SELECT total_cents FROM orders WHERE id={order_id};")
            stored_total = int(row or 0)
            return {"ok": True, "orderId": order_id, "totalCents": stored_total}
        except Exception as err:
            raise HTTPException(status_code=500, detail=str(err)) from err

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
