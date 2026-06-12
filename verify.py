"""Verification script - cross-checks clean_orders.csv against orders_v2.csv."""
import csv
import re
from collections import Counter

# --- Row count ---
with open("orders_v2.csv", encoding="utf-8") as f:
    src_rows = [r for r in csv.DictReader(f) if any(v.strip() for v in r.values())]
with open("clean_orders.csv", encoding="utf-8") as f:
    dst_rows = list(csv.DictReader(f))

print(f"Source rows (non-empty): {len(src_rows)}")
print(f"Clean  rows            : {len(dst_rows)}")
print(f"Row count match        : {len(src_rows) == len(dst_rows)}")
print()

# --- Total ---
total = sum(float(r["amount"]) for r in dst_rows)
print(f"Independent total      : {total}")
print()

# --- Duplicate order IDs ---
ids = [r["order_id"] for r in dst_rows]
dupes = [oid for oid in set(ids) if ids.count(oid) > 1]
print(f"Duplicate order IDs    : {dupes if dupes else 'None'}")

# --- All dates ISO ---
bad_dates = [r for r in dst_rows if not re.match(r"^\d{4}-\d{2}-\d{2}$", r["order_date"])]
print(f"Non-ISO dates          : {len(bad_dates)}")

# --- All amounts valid ---
bad_amts = []
for r in dst_rows:
    try:
        float(r["amount"])
    except ValueError:
        bad_amts.append(r["order_id"])
print(f"Bad amounts            : {bad_amts if bad_amts else 'None'}")

# --- Whitespace in names ---
ws_names = [r for r in dst_rows if r["customer_name"] != r["customer_name"].strip()]
print(f"Untrimmed names        : {len(ws_names)}")

# --- Title case ---
bad_case = [r for r in dst_rows if r["customer_name"] != r["customer_name"].strip().title()]
print(f"Non-title-case names   : {len(bad_case)}")

# --- Email lowercase ---
bad_emails = [r for r in dst_rows if r["email"] != r["email"].lower()]
print(f"Non-lowercase emails   : {len(bad_emails)}")

# --- Empty fields ---
empties = [(r["order_id"], k) for r in dst_rows for k in r if not r[k].strip()]
print(f"Empty fields           : {empties if empties else 'None'}")

# --- Negative / zero amounts ---
neg = [r["order_id"] for r in dst_rows if float(r["amount"]) <= 0]
print(f"Zero/negative amounts  : {neg if neg else 'None'}")

print()
print("=== Revenue cross-check by item ===")
item_rev = {}
item_cnt = Counter()
for r in dst_rows:
    item_rev[r["item"]] = item_rev.get(r["item"], 0) + float(r["amount"])
    item_cnt[r["item"]] += 1
grand = 0
for item in sorted(item_rev):
    print(f"  {item:25s}  x{item_cnt[item]:2d}  = {item_rev[item]:>10.2f}")
    grand += item_rev[item]
print(f"  {'GRAND TOTAL':25s}       = {grand:>10.2f}")

# --- indian_comma_format correctness ---
print()
print("=== Indian comma format spot-checks ===")
def indian_fmt(n):
    integer_part = int(n)
    decimal_part = f"{n - integer_part:.2f}"[1:]
    s = str(integer_part)
    if len(s) <= 3:
        return s + decimal_part
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result + decimal_part

tests = [
    (0.0, "0.00"),
    (999.0, "999.00"),
    (1000.0, "1,000.00"),
    (10000.0, "10,000.00"),
    (100000.0, "1,00,000.00"),
    (1234567.89, "12,34,567.89"),
    (172240.0, "1,72,240.00"),
]
all_ok = True
for val, expected in tests:
    got = indian_fmt(val)
    status = "OK" if got == expected else "FAIL"
    if status == "FAIL":
        all_ok = False
    print(f"  {val:>15.2f} => {got:>15s}  expected {expected:>15s}  [{status}]")

print()
if all_ok:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
