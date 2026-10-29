# Insider selling and buying in 2026, from Circle's Form 4 filings.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

rows = read('form4_transactions_2026.csv')
sales = [r for r in rows if r['code'] == 'S']
buys = [r for r in rows if r['code'] == 'P']
val = lambda rs: sum(num(r['shares']) * (num(r['price']) or 0) for r in rs)
lines = [f"Open-market sales (code S) dated 1 Jan to 27 Oct 2026: {len(sales)} transactions, {sum(num(r['shares']) for r in sales):,.0f} shares, ${val(sales) / 1e6:.1f}m",
         f"  of which in filings that cite a Rule 10b5-1 trading plan: ${val([r for r in sales if r['plan_10b5_1_footnote'] == 'yes']) / 1e6:.1f}m",
         f"Open-market purchases (code P): {len(buys)} transactions, ${val(buys) / 1e6:.1f}m"]
for a, b, n in (('2026-01-01', '2026-06-30', 'H1-26'), ('2026-07-01', '2026-09-30', 'Q3-26'), ('2026-10-01', '2026-10-31', 'Oct-26')):
    s = [r for r in sales if a <= r['date'] <= b]
    lines.append(f"  {n}: ${val(s) / 1e6:.1f}m sold")
save('insider_sales.txt', '\n'.join(lines) + '\n')
