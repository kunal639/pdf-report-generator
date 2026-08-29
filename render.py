import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from report import get_report_data


def generate_html(data: dict) -> str:
    today_str = datetime.now().strftime("%B %d, %Y")

    top_products_rows = "".join(
        f"""
        <tr>
            <td>{row['product']}</td>
            <td style="text-align: right;">{row['order_count']}</td>
            <td style="text-align: right;">${row['revenue']:,.2f}</td>
        </tr>
        """
        for row in data["top_5_products_by_revenue"]
    )

    all_orders_rows = "".join(
        f"""
        <tr>
            <td>#{row['id']}</td>
            <td>{row['customer']}</td>
            <td>{row['product']}</td>
            <td style="text-align: right;">${row['amount']:,.2f}</td>
            <td>{row['created_at'][:10]}</td>
        </tr>
        """
        for row in data["all_orders"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sales Report</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 12mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1f2937;
            margin: 0;
            padding: 0;
            font-size: 10pt;
            line-height: 1.4;
        }}
        h1 {{
            font-size: 18pt;
            margin: 0 0 4px 0;
            color: #111827;
        }}
        .date {{
            color: #6b7280;
            font-size: 9pt;
            margin-bottom: 18px;
        }}
        .metrics-grid {{
            display: table;
            width: 100%;
            margin-bottom: 20px;
        }}
        .metric-card {{
            display: table-cell;
            width: 50%;
            background-color: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 12px 16px;
        }}
        .metric-card:first-child {{
            margin-right: 12px;
        }}
        .metric-title {{
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #4b5563;
            margin-bottom: 4px;
        }}
        .metric-value {{
            font-size: 16pt;
            font-weight: 700;
            color: #111827;
        }}
        h2 {{
            font-size: 12pt;
            margin: 18px 0 8px 0;
            color: #111827;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 9pt;
        }}
        thead {{
            display: table-header-group;
        }}
        tr {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}
        th {{
            background-color: #f9fafb;
            color: #374151;
            text-align: left;
            padding: 6px 8px;
            border-bottom: 1.5px solid #d1d5db;
            font-weight: 600;
        }}
        td {{
            padding: 5px 8px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tbody tr:nth-child(even) {{
            background-color: #fafafa;
        }}
    </style>
</head>
<body>
    <h1>Executive Sales Report</h1>
    <div class="date">Generated on {today_str}</div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">Total Orders</div>
            <div class="metric-value">{data['total_orders']:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Total Revenue</div>
            <div class="metric-value">${data['total_revenue']:,.2f}</div>
        </div>
    </div>

    <h2>Top 5 Products by Revenue</h2>
    <table>
        <thead>
            <tr>
                <th>Product</th>
                <th style="text-align: right;">Orders</th>
                <th style="text-align: right;">Total Revenue</th>
            </tr>
        </thead>
        <tbody>
            {top_products_rows}
        </tbody>
    </table>

    <h2>All Orders Log</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 10%;">ID</th>
                <th style="width: 25%;">Customer</th>
                <th style="width: 35%;">Product</th>
                <th style="width: 15%; text-align: right;">Amount</th>
                <th style="width: 15%;">Date</th>
            </tr>
        </thead>
        <tbody>
            {all_orders_rows}
        </tbody>
    </table>
</body>
</html>
"""


def render_pdf_sync(output_path: str = "reports/test.pdf") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data = get_report_data()
    html_content = generate_html(data)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()

    return output_path


if __name__ == "__main__":
    render_pdf_sync()