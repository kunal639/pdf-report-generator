import sqlite3
import random
from datetime import datetime, timedelta, timezone

DB_PATH = "report.db"

CUSTOMERS = [
    "Alice Smith",
    "Bob Jones",
    "Charlie Brown",
    "Diana Prince",
    "Evan Wright",
    "Fiona Gallagher",
]

PRODUCTS = [
    "Wireless Mouse",
    "Mechanical Keyboard",
    "USB-C Hub",
    "Noise-Cancelling Headphones",
    "Laptop Stand",
    "Desk Mat",
]


def seed_database(num_records: int = 200):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    )

    # Wipe existing records to ensure idempotency (safe to run multiple times)
    cursor.execute("DELETE FROM orders")

    now = datetime.now(timezone.utc)
    orders = []

    for _ in range(num_records):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5.0, 200.0), 2)
        random_days_ago = random.uniform(0, 30)
        created_at = (now - timedelta(days=random_days_ago)).isoformat()

        orders.append((customer, product, amount, created_at))

    cursor.executemany(
        """
        INSERT INTO orders (customer, product, amount, created_at)
        VALUES (?, ?, ?, ?)
    """,
        orders,
    )

    conn.commit()

    # Verification checkpoint
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_rows = cursor.fetchone()[0]
    print(f"Seeding complete. SELECT COUNT(*) -> {total_rows} orders")

    conn.close()


if __name__ == "__main__":
    seed_database(200)