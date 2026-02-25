#!/usr/bin/env python3
"""
Plot monthly link creation counts for the past 12 months.

Dependencies (install if missing):
    pip install psycopg2-binary matplotlib python-dotenv

Usage:
    python plot_monthly_links.py [output_path]

Arguments:
    output_path  Path for the output PNG file (default: monthly_links_chart.png)
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone


def find_env_file():
    """Search current directory and up to 4 parent directories for a .env file."""
    current = Path.cwd()
    for candidate in [current] + list(current.parents)[:4]:
        for name in (".env.local", ".env"):
            path = candidate / name
            if path.exists():
                return path
    return None


def load_database_url():
    """Load DATABASE_URL from .env file or environment variable."""
    env_path = find_env_file()
    if env_path:
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path, override=False)
        except ImportError:
            # Manually parse the .env file if python-dotenv is unavailable
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        value = line[len("DATABASE_URL="):]
                        # Strip surrounding quotes if present
                        if value and value[0] in ('"', "'"):
                            value = value[1:-1]
                        os.environ.setdefault("DATABASE_URL", value)
                        break

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in environment or .env file.")
        print(f"Searched from: {Path.cwd()}")
        sys.exit(1)
    return db_url


def query_monthly_counts(db_url):
    """Query the links table and return (month_label, count) for the past 12 months."""
    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2 is not installed.")
        print("Install it with: pip install psycopg2-binary")
        sys.exit(1)

    sql = """
        SELECT
            TO_CHAR(DATE_TRUNC('month', created_at AT TIME ZONE 'UTC'), 'Mon YYYY') AS month_label,
            DATE_TRUNC('month', created_at AT TIME ZONE 'UTC') AS month_start,
            COUNT(*) AS link_count
        FROM links
        WHERE created_at >= NOW() - INTERVAL '12 months'
        GROUP BY month_start, month_label
        ORDER BY month_start ASC;
    """

    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    finally:
        conn.close()

    return [(row[0], int(row[2])) for row in rows]


def fill_missing_months(data):
    """Ensure all 12 months are represented, even if count is 0."""
    from datetime import date
    import calendar

    today = datetime.now(timezone.utc)
    months = []
    for i in range(11, -1, -1):
        # Calculate month offset
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        dt = date(year, month, 1)
        label = dt.strftime("%b %Y")
        months.append(label)

    counts_by_label = dict(data)
    return [(m, counts_by_label.get(m, 0)) for m in months]


def plot_chart(data, output_path):
    """Generate and save the bar chart as a PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend for file output
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        print("Error: matplotlib is not installed.")
        print("Install it with: pip install matplotlib")
        sys.exit(1)

    labels = [d[0] for d in data]
    counts = [d[1] for d in data]

    fig, ax = plt.subplots(figsize=(14, 6))

    bars = ax.bar(labels, counts, color="#4F81BD", edgecolor="white", linewidth=0.6)

    # Value labels on top of each bar
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts) * 0.01,
                str(count),
                ha="center",
                va="bottom",
                fontsize=9,
                color="#333333",
            )

    ax.set_title("Links Created — Past 12 Months", fontsize=16, fontweight="bold", pad=16)
    ax.set_xlabel("Month", fontsize=12, labelpad=10)
    ax.set_ylabel("Links Created", fontsize=12, labelpad=10)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_ylim(0, max(counts) * 1.15 if max(counts) > 0 else 10)

    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved to: {Path(output_path).resolve()}")


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "monthly_links_chart.png"

    print("Loading database credentials...")
    db_url = load_database_url()

    print("Querying link counts for the past 12 months...")
    raw_data = query_monthly_counts(db_url)

    data = fill_missing_months(raw_data)
    total = sum(c for _, c in data)
    print(f"Total links in period: {total}")

    print("Generating chart...")
    plot_chart(data, output_path)


if __name__ == "__main__":
    main()
