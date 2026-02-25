---
name: monthly-links-chart
description: Generates a bar chart PNG showing the number of links created each month for the past 12 months. Queries the project PostgreSQL database using DATABASE_URL from the .env file. Use when the user asks to visualise, chart, or plot link creation statistics, monthly link counts, or link analytics over time.
---

# Monthly Links Chart

## Overview

Queries the `links` table for records created in the past 12 months, groups them by calendar month, and produces a bar chart exported as a PNG using `scripts/plot_monthly_links.py`.

## Dependencies

Requires Python 3.8+ and the following packages:

```bash
pip install psycopg2-binary matplotlib python-dotenv
```

## Usage

Run the script from anywhere inside the project directory. It automatically locates the `.env` or `.env.local` file by walking up the directory tree.

```bash
python3 .agents/skills/monthly-links-chart/scripts/plot_monthly_links.py [output_path]
```

- `output_path` — optional; defaults to `monthly_links_chart.png` in the current working directory.

Example with explicit output path:

```bash
python3 .agents/skills/monthly-links-chart/scripts/plot_monthly_links.py charts/links_2026.png
```

## What the Script Does

1. Locates `.env` / `.env.local` and reads `DATABASE_URL`
2. Connects to the PostgreSQL database (Neon)
3. Runs a `GROUP BY month` query on `links.created_at` for the past 12 months
4. Fills in any months with zero links so all 12 months always appear on the chart
5. Plots a bar chart (x-axis: month labels, y-axis: link count) with count labels above each bar
6. Saves the chart as a PNG at the specified output path

## Database Schema Reference

The script queries the `links` table using the `created_at TIMESTAMPTZ` column, grouping by `DATE_TRUNC('month', created_at AT TIME ZONE 'UTC')` to ensure UTC-consistent monthly bucketing.
