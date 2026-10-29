# Long Coinbase, short Circle: how much of CRCL's daily move does COIN explain, and does adding bitcoin help?
# If the leftover noise is much bigger than the edge, it isn't a trade.
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, save

px = read('prices_daily.csv')
final = {r['ticker']: num(r['close']) for r in read('closes_2026-10-28.csv')}
btc = {r['date']: num(r['btc_usd']) for r in read('btc_daily_yahoo.csv')}
rows = []
for r in px:
    c, k = num(r['CRCL']), num(r['COIN'])
    if r['date'] == '2026-10-28': c, k = final['CRCL'], final['COIN']     # session pull replaced by the close
    if r['date'] in btc: rows.append((r['date'], c, k, btc[r['date']]))


def ols(y, X):
    # least squares with an intercept, by the normal equations
    n, m = len(y), len(X[0]) + 1
    Z = [[1.0] + list(x) for x in X]
    A = [[sum(Z[t][i] * Z[t][j] for t in range(n)) for j in range(m)] + [sum(Z[t][i] * y[t] for t in range(n))] for i in range(m)]
    for c in range(m):
        p = max(range(c, m), key=lambda r: abs(A[r][c])); A[c], A[p] = A[p], A[c]
        for r in range(m):
            if r != c:
                f = A[r][c] / A[c][c]; A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    b = [A[i][m] / A[i][i] for i in range(m)]
    res = [y[t] - sum(b[i] * Z[t][i] for i in range(m)) for t in range(n)]
    my = sum(y) / n
    r2 = 1 - sum(e * e for e in res) / sum((v - my) ** 2 for v in y)
    vol = math.sqrt(sum(e * e for e in res) / (n - m)) * math.sqrt(252)
    return b[1:], r2, vol


L = []
for win in (60, 125, 250):
    w = rows[-win - 1:]
    lr = lambda i: [math.log(w[t + 1][i] / w[t][i]) for t in range(len(w) - 1)]
    c, k, b = lr(1), lr(2), lr(3)
    bk, r2k, vk = ols(c, [[x] for x in k])
    bkb, r2kb, vkb = ols(c, [[x, z] for x, z in zip(k, b)])
    L.append(f'{win} days: CRCL on COIN beta {bk[0]:.2f}, R2 {r2k:.2f}, residual vol {vk:.1%} a year ({vk / math.sqrt(12):.1%} a month); '
             f'adding bitcoin: betas {bkb[0]:.2f}/{bkb[1]:.2f}, residual vol {vkb:.1%}')
L.append(f"CRCL/COIN price ratio at the 28 Oct close: {final['CRCL'] / final['COIN']:.3f}")
save('pair_hedge.txt', '\n'.join(L) + '\n')
