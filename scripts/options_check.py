# What the options market says, as an outside check on my scenario weights.
# Risk-neutral odds, so they lean a bit low on upside versus real-world odds. Two ways:
# call-spread slopes between the most traded strikes, and a lognormal at the median implied vol.
import os, sys, math, statistics, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

rows = read('crcl_options_20261028.csv')
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'crcl_options_20261028.csv')) as f:
    head = f.readline()
S = float(head.split('underlying ')[1].split(')')[0])
NOW = dt.date(2026, 10, 28)
R = 0.045
L = [f'CRCL {S} at the snapshot']
def chain(exp, typ):
    return {num(r['strike']): r for r in rows if r['expiry'] == exp and r['type'] == typ and num(r['bid']) > 0 and num(r['ask']) > 0}
def mid(r): return (num(r['bid']) + num(r['ask'])) / 2
ncdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
for exp in ('20280121', '20290119'):
    T = (dt.date(int(exp[:4]), int(exp[4:6]), int(exp[6:])) - NOW).days / 365
    c = chain(exp, 'C')
    near = [k for k in c if 0.8 * S <= k <= 1.25 * S]
    iv = statistics.median(num(c[k]['iv']) for k in near)
    L.append(f'{exp}: {T:.2f} years, median implied vol near the money {iv:.0%}')
    for k1, k2 in ((80, 100), (100, 150), (150, 200), (200, 230)):
        if k1 in c and k2 in c:
            p = (mid(c[k1]) - mid(c[k2])) / (k2 - k1) * math.exp(R * T)
            L.append(f'  call spread {k1}-{k2}: odds of finishing above ~{(k1 + k2) / 2:.0f} = {p:.1%}')
    for K in (58, 100, 150, 200, 255):
        d2 = (math.log(S / K) + (R - iv * iv / 2) * T) / (iv * math.sqrt(T))
        L.append(f'  lognormal at {iv:.0%}: P(above ${K}) = {ncdf(d2):.1%}')
# The move the market is pricing for the 4 Nov print: at-the-money straddle on the 6 Nov expiry
c, p = chain('20261106', 'C'), chain('20261106', 'P')
k = min((k for k in c if k in p), key=lambda k: abs(k - S))
L.append(f'6 Nov expiry, ${k:.0f} straddle: ${mid(c[k]) + mid(p[k]):.2f}, about {(mid(c[k]) + mid(p[k])) / S:.1%} either way through the print')
save('options_check.txt', '\n'.join(L) + '\n')
