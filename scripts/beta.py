# Beta and cost of equity for the discount rate. Weekly returns over the last year against SPY (daily betas are inflated
# by noise for a stock this volatile; both are printed), the usual Blume adjustment (0.67 x raw + 0.33), and CAPM.
import os, sys, statistics as st, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save, RESULTS

px = read('prices_daily.csv')
ce = {r['item']: num(r['value']) for r in read('cost_of_equity.csv')}
def beta(sym, start='2025-10-28', step=5):
    rows = [r for r in px if r['date'] >= start and r[sym] and r['SPY']]
    rows = rows[::step]
    r = [(num(b[sym]) / num(a[sym]) - 1, num(b['SPY']) / num(a['SPY']) - 1) for a, b in zip(rows, rows[1:])]
    ys, xs = [a for a, _ in r], [b for _, b in r]
    mx, my = st.mean(xs), st.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs), len(r)
L = []
for s in ('CRCL', 'COIN', 'HOOD', 'PYPL', 'V', 'MA'):
    bw, n = beta(s); bd, nd = beta(s, step=1)
    L.append(f'{s}: weekly beta {bw:.2f} ({n} weeks), daily {bd:.2f}')
b = beta('CRCL')[0]
adj = 0.67 * b + 0.33
coe_adj = ce['risk_free_10y_pct'] + adj * ce['equity_risk_premium_pct']
coe_raw = ce['risk_free_10y_pct'] + b * ce['equity_risk_premium_pct']
L.append(f'CRCL weekly beta {b:.2f}, Blume-adjusted {adj:.2f}; cost of equity = {ce["risk_free_10y_pct"]}% + {adj:.2f} x {ce["equity_risk_premium_pct"]}% = {coe_adj:.1f}% '
         f'(raw beta: {coe_raw:.1f}%). Circle has no debt, so this is the discount rate.')
save('beta.txt', '\n'.join(L) + '\n')
with open(os.path.join(RESULTS, 'cost_of_equity.csv'), 'w') as fh:
    fh.write(f'item,value\ncoe_adjusted_pct,{coe_adj:.2f}\ncoe_raw_pct,{coe_raw:.2f}\nbeta_weekly,{b:.3f}\nbeta_adjusted,{adj:.3f}\n')
