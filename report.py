import json
import sqlite3
from typing import Any, Dict

DB_PATH = "report.db"


def get_report_data(db_path: str = DB_PATH) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Total number of orders
    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cursor.fetchone()["total_orders"]

    # 2. Total revenue
    cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS total_revenue FROM orders")
    total_revenue = round(cursor.fetchone()["total_revenue"], 2)

    # 3. Top 5 products by revenue
    cursor.execute(
        """
        SELECT 
            product,
            ROUND(SUM(amount), 2) AS revenue,
            COUNT(*) AS order_count
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
        """
    )
    top_products = [dict(row) for row in cursor.fetchall()]

    # 4. Orders per day for the last 7 days
    cursor.execute(
        """
        SELECT 
            DATE(created_at) AS order_date,
            COUNT(*) AS order_count,
            ROUND(SUM(amount), 2) AS daily_revenue
        FROM orders
        WHERE created_at >= DATETIME('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY order_date ASC
        """
    )
    daily_orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_5_products_by_revenue": top_products,
        "orders_last_7_days": daily_orders,
    }


if __name__ == "__main__":
    report = get_report_data()
    print(json.dumps(report, indent=2))