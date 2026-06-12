"""
clean_orders.py  -  Normalise a messy orders CSV and produce a clean report.

Production-grade script featuring:
- Command-line arguments for flexible execution
- Standardized logging instead of print statements
- Modular functions for easier testing and maintenance
- Error handling for missing files and malformed data rows
"""

import argparse
import csv
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# -- setup logging -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# -- helpers -----------------------------------------------------------------
def normalise_date(raw: str) -> str:
    """Convert any of the three observed date formats to ISO-8601 (YYYY-MM-DD)."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Empty date string")

    formats = [
        "%Y-%m-%d",  # 2026-03-22
        "%d/%m/%Y",  # 15/03/2026
        "%b %d, %Y", # Apr 10, 2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"Unrecognised date format: '{raw}'")


def normalise_amount(raw: str) -> float:
    """Strip currency prefixes (Rs., INR) and commas, return a plain float."""
    cleaned = raw.strip()
    if not cleaned:
        raise ValueError("Empty amount string")
        
    cleaned = re.sub(r"(?i)^(rs\.?|inr)\s*", "", cleaned)  # remove prefix
    cleaned = cleaned.replace(",", "")                       # remove commas
    try:
        return float(cleaned)
    except ValueError as e:
        raise ValueError(f"Could not parse amount '{raw}': {e}")


def normalise_name(raw: str) -> str:
    """Trim whitespace and convert to Title Case."""
    return raw.strip().title()


def indian_comma_format(n: float) -> str:
    """
    Format a number with Indian comma grouping.
    E.g.  1234567.50  ->  12,34,567.50
    """
    integer_part = int(n)
    decimal_part = f"{abs(n) - abs(integer_part):.2f}"[1:]  # ".50"

    s = str(abs(integer_part))
    if len(s) <= 3:
        formatted = s + decimal_part
        return f"-{formatted}" if n < 0 else formatted

    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]

    formatted = result + decimal_part
    return f"-{formatted}" if n < 0 else formatted


# -- core processing ---------------------------------------------------------
def process_orders(input_path: Path) -> List[Dict[str, Any]]:
    """Read raw orders, clean the data, and return a list of parsed dictionaries."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    clean_rows: List[Dict[str, Any]] = []
    skipped_rows = 0

    try:
        with input_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2): # start=2 for header + 1-based indexing
                # Skip completely empty rows
                if not any(v.strip() for v in row.values()):
                    continue

                try:
                    clean_rows.append({
                        "order_id":      row["order_id"].strip(),
                        "order_date":    normalise_date(row["order_date"]),
                        "customer_name": normalise_name(row["customer_name"]),
                        "email":         row["email"].strip().lower(),
                        "item":          row["item"].strip(),
                        "amount":        round(normalise_amount(row["amount"]), 2),
                    })
                except Exception as e:
                    logger.warning(f"Skipping malformed row {row_idx}: {e}")
                    skipped_rows += 1
                    
    except Exception as e:
        logger.error(f"Failed to process {input_path}: {e}")
        sys.exit(1)

    logger.info(f"Successfully processed {len(clean_rows)} rows. Skipped {skipped_rows} rows.")
    return clean_rows


def export_clean_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Export the cleaned orders to a new CSV file."""
    if not rows:
        logger.warning("No rows to export. CSV will be empty.")
        
    fieldnames = ["order_id", "order_date", "customer_name", "email", "item", "amount"]
    try:
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Clean CSV exported to: {output_path}")
    except IOError as e:
        logger.error(f"Failed to write to {output_path}: {e}")
        sys.exit(1)


def generate_report(rows: List[Dict[str, Any]], report_path: Path, source_name: str) -> None:
    """Generate a markdown report with summary statistics."""
    if not rows:
        logger.warning("No data available to generate report.")
        return

    # Compute stats
    total_value    = sum(r["amount"] for r in rows)
    total_orders   = len(rows)
    unique_custs   = len({r["customer_name"] for r in rows})

    item_counts    = Counter(r["item"] for r in rows)
    top_item, top_count = item_counts.most_common(1)[0]

    item_revenue: Dict[str, float] = {}
    for r in rows:
        item_revenue[r["item"]] = item_revenue.get(r["item"], 0) + r["amount"]

    dates = [r["order_date"] for r in rows]
    date_range = f"{min(dates)} to {max(dates)}"

    fmt_total = indian_comma_format(total_value)

    # Build report lines
    lines = [
        "# Orders Report", "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Source file:** `{source_name}`", "",
        "---", "",
        "## Summary", "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total Orders | {total_orders} |",
        f"| Unique Customers | {unique_custs} |",
        f"| Total Order Value | Rs. {fmt_total} |",
        f"| Date Range | {date_range} |",
        f"| Most Popular Item | {top_item} ({top_count} orders) |", "",
        "---", "",
        "## Revenue by Item", "",
        "| Item | Orders | Revenue |",
        "|---|---|---|"
    ]

    for item, count in item_counts.most_common():
        rev = indian_comma_format(item_revenue[item])
        lines.append(f"| {item} | {count} | Rs. {rev} |")
    
    lines.extend([
        "", "---", "",
        "## Top 10 Orders by Value", "",
        "| Order ID | Date | Customer | Email | Item | Amount |",
        "|---|---|---|---|---|---|"
    ])

    top_orders = sorted(rows, key=lambda r: r["amount"], reverse=True)[:10]
    for r in top_orders:
        amt = indian_comma_format(r["amount"])
        lines.append(
            f"| {r['order_id']} | {r['order_date']} | {r['customer_name']} "
            f"| {r['email']} | {r['item']} | Rs. {amt} |"
        )
    
    lines.extend([
        "", "---", "",
        f"*Clean data exported successfully.*", ""
    ])

    try:
        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Report written to: {report_path}")
    except IOError as e:
        logger.error(f"Failed to write report to {report_path}: {e}")
        sys.exit(1)


# -- cli entrypoint ----------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalise a messy orders CSV and produce a clean report.")
    parser.add_argument(
        "-i", "--input", 
        type=Path, 
        default=Path("orders_v2.csv"),
        help="Path to the input raw CSV file (default: orders_v2.csv)"
    )
    parser.add_argument(
        "-o", "--output", 
        type=Path, 
        default=Path("clean_orders.csv"),
        help="Path to the output cleaned CSV file (default: clean_orders.csv)"
    )
    parser.add_argument(
        "-r", "--report", 
        type=Path, 
        default=Path("report.md"),
        help="Path to the output Markdown report (default: report.md)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # 1. Read and clean the data
    logger.info(f"Starting processing for {args.input.name}...")
    clean_rows = process_orders(args.input)
    
    if not clean_rows:
        logger.warning("No valid data processed. Exiting.")
        sys.exit(0)

    # 2. Export to CSV
    export_clean_csv(clean_rows, args.output)
    
    # 3. Generate summary report
    generate_report(clean_rows, args.report, args.input.name)
    
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
