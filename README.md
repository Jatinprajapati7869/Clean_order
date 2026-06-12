# Clean Order Data Processor

A production-grade Python utility for normalizing messy order datasets into a clean, standardized format and generating automated analytical reports.

## Features

- **Data Normalization**: Intelligently converts mixed date formats into standard ISO-8601 (`YYYY-MM-DD`).
- **Currency Formatting**: Cleans and formats raw amounts into precise Indian Rupee (INR) comma grouping (e.g., `1,72,240.00`).
- **Text Cleaning**: Automatically trims whitespaces, normalizes email casings, and title-cases customer names.
- **Fault Tolerance**: Safely skips malformed rows and handles missing data without crashing the pipeline.
- **Automated Reporting**: Generates a professional Markdown (`.md`) summary report with key statistics, revenue breakdowns by item, and top orders.

## Getting Started

### Prerequisites
- Python 3.7+
- No external dependencies required (uses only standard libraries).

### Usage

Run the script from the command line. You can optionally specify input and output paths.

```bash
# Run with default files (orders_v2.csv)
python clean_orders.py

# Run with custom input and output paths
python clean_orders.py --input raw_data.csv --output cleaned_data.csv --report monthly_summary.md
```

### Verification
A standalone verification script is included to ensure complete data integrity.

```bash
python verify.py
```

## Structure
- `clean_orders.py`: Core processing pipeline.
- `verify.py`: Integrity checks for row counts, amount calculations, and data formatting.
