# Binance's USDC from two independent places: Binance's own monthly proof-of-reserves reports,
# and DefiLlama's daily tracking of Binance's labelled wallets.
import os, sys, datetime as dt, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

por = {dt.date.fromisoformat(r['snapshot']): r for r in read('binance_por_usdc.csv')}
ll = {dt.date.fromisoformat(r['date']): num(r['usdc_usd']) / 1e6 for r in read('binance_wallets_usdc_defillama.csv')}
lines = ['Month start: Binance proof of reserves (customers / total held) against DefiLlama wallets, $bn']
for k in sorted(por):
    if k >= dt.date(2025, 7, 1):
        lines.append(f"  {k}: {num(por[k]['customer_liability_musd']) / 1e3:5.2f} / {num(por[k]['binance_holdings_musd']) / 1e3:5.2f} | DefiLlama {ll.get(k, float('nan')) / 1e3:5.2f}")
peak = max(por, key=lambda k: num(por[k]['binance_holdings_musd']))
lines.append(f"Proof-of-reserves peak: ${num(por[peak]['binance_holdings_musd']) / 1e3:.2f}bn on {peak}; latest ${num(por[max(por)]['binance_holdings_musd']) / 1e3:.2f}bn on {max(por)}")
lpk = max(ll, key=ll.get)
lines.append(f"DefiLlama peak: ${ll[lpk] / 1e3:.2f}bn on {lpk}; latest ${ll[max(ll)] / 1e3:.2f}bn on {max(ll)}")

def trap(a, b, col):
    pts = [num(por[k][col]) for k in sorted(por) if a <= k <= b]
    return (pts[0] / 2 + sum(pts[1:-1]) + pts[-1] / 2) / (len(pts) - 1)
def dl(a, b):
    return statistics.mean(v for k, v in ll.items() if a <= k <= b)
q2a, q2b, q3a, q3b = dt.date(2026, 4, 1), dt.date(2026, 6, 30), dt.date(2026, 7, 1), dt.date(2026, 9, 30)
for col, name in (('customer_liability_musd', 'customers'), ('binance_holdings_musd', 'total held')):
    a, b = trap(q2a, dt.date(2026, 7, 1), col), trap(q3a, dt.date(2026, 10, 1), col)
    lines.append(f"Proof of reserves, {name}: Q2-26 average ${a / 1e3:.2f}bn, Q3-26 ${b / 1e3:.2f}bn ({b / a - 1:+.1%})")
a, b = dl(q2a, q2b), dl(q3a, q3b)
lines.append(f"DefiLlama wallets: Q2-26 average ${a / 1e3:.2f}bn, Q3-26 ${b / 1e3:.2f}bn ({b / a - 1:+.1%})")
cpk = max(por, key=lambda k: num(por[k]['customer_liability_musd']))
lines.append(f"Customer USDC peak: ${num(por[cpk]['customer_liability_musd']) / 1e3:.2f}bn on {cpk}; ${num(por[max(por)]['customer_liability_musd']) / 1e3:.2f}bn on {max(por)}")
gaps = [abs(ll[k] - num(por[k]['binance_holdings_musd'])) for k in por if k >= dt.date(2026, 1, 1) and k in ll]
lines.append(f"DefiLlama vs Binance's own total, month starts in 2026: largest gap ${max(gaps) / 1e3:.2f}bn")

# What is left of Circle's own platform if all of Binance's customer USDC sits on Circle's side (an assumption, see README)
circ = {r['quarter']: r for r in read('circle_quarterly.csv')}
qs = {'Q3-25': (dt.date(2025, 7, 1), dt.date(2025, 10, 1)), 'Q4-25': (dt.date(2025, 10, 1), dt.date(2026, 1, 1)),
      'Q1-26': (dt.date(2026, 1, 1), dt.date(2026, 4, 1)), 'Q2-26': (dt.date(2026, 4, 1), dt.date(2026, 7, 1))}
q4_avg, q4_onp = 76.19, 15.6  # derived from 10-K full-year figures in yield_split.py
for k, (a, b) in qs.items():
    if k == 'Q4-25':
        plat = q4_avg * q4_onp / 100
    else:
        plat = num(circ[k]['usdc_avg_bn']) * num(circ[k]['circle_on_platform_pct']) / 100
    bc = trap(a, b, 'customer_liability_musd') / 1e3
    lines.append(f"  {k}: Circle's own platform ${plat:.2f}bn average, Binance customers ${bc:.2f}bn, the rest ${plat - bc:.2f}bn")

# Circle's prospectus said USDC was 5%, 10% and 18% of stablecoins held on Binance at 1 Jul 2024, 1 Jan 2025 and 1 Apr 2025.
for r in read('binance_por_stablecoins_check.csv'):
    tot = sum(num(r[c]) for c in ('usdt', 'fdusd', 'usdc', 'tusd', 'busd'))
    lines.append(f"  check against Circle's prospectus, {r['snapshot']}: USDC is {num(r['usdc']) / tot:.1%} of the stablecoins Binance held")
save('binance_balances.txt', '\n'.join(lines) + '\n')

# Chart data: Binance's USDC from both sources, month starts
out = ['Month,Binance proof of reserves: customers ($bn),Binance proof of reserves: total held ($bn),DefiLlama Binance wallets ($bn)']
for k in sorted(por):
    if k >= dt.date(2025, 1, 1):
        out.append(f"{k},{num(por[k]['customer_liability_musd']) / 1e3:.2f},{num(por[k]['binance_holdings_musd']) / 1e3:.2f},{ll.get(k, 0) / 1e3:.2f}")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'chart7_binance_usdc.csv'), 'w') as fh:
    fh.write('\n'.join(out) + '\n')
