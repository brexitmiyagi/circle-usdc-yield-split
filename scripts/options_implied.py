# The odds the CRCL options market puts on the stock finishing above any price at an expiry (risk-neutral).
# Mid prices are noisy, so I smooth the implied-vol smile first: a quadratic in log-moneyness fitted to the quoted vols,
# weighted by open interest, then price calls off the smooth smile and take the slope (Breeden-Litzenberger).
# Risk-neutral odds put more weight on bad outcomes than real-world odds do, so they understate the upside a holder faces.
import os, sys, math, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, DATA

FILE = 'crcl_options_20261028.csv'
rows = read(FILE)
with open(os.path.join(DATA, FILE)) as f:
    S = float(f.readline().split('underlying ')[1].split(')')[0])
NOW = dt.date(2026, 10, 28)
R = 0.045            # about the 1-year bill on the snapshot day
ncdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def years(exp):
    return (dt.date(int(exp[:4]), int(exp[4:6]), int(exp[6:])) - NOW).days / 365


def smile(exp):
    T = years(exp); F = S * math.exp(R * T)
    pts = [(math.log(num(r['strike']) / F), num(r['iv']), max(1.0, num(r['open_interest'])))
           for r in rows if r['expiry'] == exp and r['type'] == 'C' and num(r['bid']) > 0 and num(r['ask']) > 0
           and 0.3 * S <= num(r['strike']) <= 4 * S and 0.2 < num(r['iv']) < 3]
    # weighted least squares, iv = a + b x + c x^2
    sw = [[0.0] * 3 for _ in range(3)]; sy = [0.0] * 3
    for x, v, w in pts:
        b = [1, x, x * x]
        for i in range(3):
            sy[i] += w * b[i] * v
            for j in range(3): sw[i][j] += w * b[i] * b[j]
    n = 3; M = [sw[i][:] + [sy[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]; M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    a, b, c = (M[i][n] / M[i][i] for i in range(n))
    return lambda K: a + b * math.log(K / F) + c * math.log(K / F) ** 2, len(pts)


def call(K, T, iv):
    d1 = (math.log(S / K) + (R + iv * iv / 2) * T) / (iv * math.sqrt(T)); d2 = d1 - iv * math.sqrt(T)
    return S * ncdf(d1) - K * math.exp(-R * T) * ncdf(d2)


def prob_above(K, exp='20280121'):
    T = years(exp); iv, _ = smile(exp); h = 0.5
    return -(call(K + h, T, iv(K + h)) - call(K - h, T, iv(K - h))) / (2 * h) * math.exp(R * T)
