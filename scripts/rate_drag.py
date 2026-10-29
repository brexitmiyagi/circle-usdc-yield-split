# How much stablecoin float do higher bill rates cost? USDC pays its holders nothing, so when bills pay more, holding it
# costs more. valuation.py and model.py take float off each scenario when the forward curve puts the reserve return above
# today's. This script estimates that drag from the data instead of assuming it.
# Monthly, Jan 2019 to Sep 2026: change in log supply (month-end) on the change in the 3-month bill (this month and the
# five before, so the sum is the six-month effect), with bitcoin's return this month and last as the crypto control.
# Standard errors are Newey-West with six lags. Run for all stablecoins and for USDC, full sample and 2023 onward.
import os, sys, math, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, save, RESULTS

bill = {r['month']: float(r['bill_3m_pct']) for r in read('treasury_3m_monthly.csv')}
btc = {r['month']: float(r['btc_close']) for r in read('btc_monthly_yahoo.csv')}
allsc = {r['month']: float(r['all_stablecoins_usd']) for r in read('stablecoins_total_monthend.csv')}
usdc = {}
for r in read('usdc_supply_history.csv'):
    usdc[r['date'][:7]] = float(r['usdc_usd'])          # last day seen in each month = month-end
LAST = '2026-09'                                         # October is not finished


def months(a, b):
    y, m = int(a[:4]), int(a[5:]); out = []
    while f'{y}-{m:02d}' <= b:
        out.append(f'{y}-{m:02d}'); m += 1
        if m == 13: y, m = y + 1, 1
    return out


def prev(k, n=1):
    y, m = int(k[:4]), int(k[5:]) - n
    while m < 1: y, m = y - 1, m + 12
    return f'{y}-{m:02d}'


def solve(A, b):
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def inv(A):
    n = len(A)
    return list(map(list, zip(*[solve(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)])))


def ols_nw(Y, X, L=6):
    n, k = len(Y), len(X[0])
    XtX = [[sum(X[t][i] * X[t][j] for t in range(n)) for j in range(k)] for i in range(k)]
    b = solve(XtX, [sum(X[t][i] * Y[t] for t in range(n)) for i in range(k)])
    e = [Y[t] - sum(X[t][i] * b[i] for i in range(k)) for t in range(n)]
    S = [[sum(e[t] ** 2 * X[t][i] * X[t][j] for t in range(n)) for j in range(k)] for i in range(k)]
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        for i in range(k):
            for j in range(k):
                S[i][j] += w * sum(e[t] * e[t - l] * (X[t][i] * X[t - l][j] + X[t - l][i] * X[t][j]) for t in range(l, n))
    Ai = inv(XtX)
    V = [[sum(Ai[i][p] * S[p][q] * Ai[q][j] for p in range(k) for q in range(k)) for j in range(k)] for i in range(k)]
    r2 = 1 - sum(x * x for x in e) / sum((y - sum(Y) / n) ** 2 for y in Y)
    return b, V, r2


LAGS = 6
def run(series, start, label):
    Y, X = [], []
    for k in months(start, LAST):
        need = [k, prev(k)] + [prev(k, j) for j in range(1, LAGS + 1)] + [prev(k, 2)]
        if not all(m in series for m in (k, prev(k))) or not all(m in bill for m in need) or not all(m in btc for m in (k, prev(k), prev(k, 2))):
            continue
        Y.append(100 * math.log(series[k] / series[prev(k)]))
        row = [1.0] + [bill[prev(k, j)] - bill[prev(k, j + 1)] for j in range(LAGS)]
        row += [100 * math.log(btc[k] / btc[prev(k)]), 100 * math.log(btc[prev(k)] / btc[prev(k, 2)])]
        X.append(row)
    b, V, r2 = ols_nw(Y, X)
    idx = list(range(1, LAGS + 1))
    s = sum(b[i] for i in idx); se = math.sqrt(sum(V[i][j] for i in idx for j in idx))
    return dict(label=label, n=len(Y), sum=s, se=se, t=s / se, lo=s - 1.96 * se, hi=s + 1.96 * se, btc=b[LAGS + 1], r2=r2)


out = [run(allsc, '2019-03', 'All stablecoins, Mar 2019 to Sep 2026'), run(usdc, '2019-03', 'USDC, Mar 2019 to Sep 2026'),
       run(allsc, '2023-01', 'All stablecoins, Jan 2023 to Sep 2026'), run(usdc, '2023-01', 'USDC, Jan 2023 to Sep 2026')]
L = ['Six-month effect of +1.00pt on the 3-month bill, % change in supply (Newey-West 95% range), bitcoin held constant:']
for o in out:
    L.append(f"  {o['label']} ({o['n']} months): {o['sum']:+.1f}% (t {o['t']:.1f}; {o['lo']:+.1f}% to {o['hi']:+.1f}%), bitcoin +10% -> {10 * o['btc']:+.2f}%, R2 {o['r2']:.2f}")
L.append('Robustness, all stablecoins, by number of monthly lags (sum, 95% range):')
for lags in (2, 3, 6, 9, 12):
    LAGS = lags
    a, c = run(allsc, '2019-03', ''), run(allsc, '2023-01', '')
    L.append(f"  {lags:2d} lags: full sample {a['sum']:+.1f}% ({a['lo']:+.1f}% to {a['hi']:+.1f}%), 2023 onward {c['sum']:+.1f}% ({c['lo']:+.1f}% to {c['hi']:+.1f}%)")
LAGS = 6
# Base: all stablecoins since 2023. It is the regime the forecasts start from (after Terra and FTX), it barely moves with the
# lag length, and it is the smaller of the two. The full sample leans on 2022, when rates and the crypto crash hit together.
base, full = out[2], out[0]
drag = max(0.0, -base['sum'])
L.append(f"Drag used in valuation.py and model.py: {drag:.1f}% of float per 1.00pt of bill rate, both directions (all stablecoins since 2023; USDC share held).")
L.append(f"Sensitivities: the 95% range {max(0.0, -base['hi']):.1f}% to {max(0.0, -base['lo']):.1f}%, the full-sample {-full['sum']:.1f}%, and zero.")
save('rate_drag.txt', '\n'.join(L) + '\n')
with open(os.path.join(RESULTS, 'rate_drag.csv'), 'w') as fh:
    fh.write('item,value\n')
    fh.write(f"drag_per_100bp_pct,{drag:.2f}\ndrag_low_pct,{max(0.0, -base['hi']):.2f}\ndrag_high_pct,{max(0.0, -base['lo']):.2f}\ndrag_full_sample_pct,{-full['sum']:.2f}\n")
    for o in out:
        fh.write(f"\"{o['label']} sum\",{o['sum']:.3f}\n\"{o['label']} se\",{o['se']:.3f}\n")
