# Does the options market already price my view of the 4 November report? Checks one trade: the 20 Nov $80/$70 put spread.
# Market odds: implied vol fitted across out-of-the-money puts and calls (quadratic in log-moneyness, weighted by open
# interest), then read off as a distribution (Breeden-Litzenberger). My odds: a scenario tree from reaction_study.py,
# written out below so anyone can change it. Quotes are the 28 Oct close.
import os, sys, math, random, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, DATA, save

import glob
FILE = os.path.basename(sorted(glob.glob(os.path.join(DATA, 'crcl_options_*_close.csv')))[-1])   # the latest close on file
rows = read(FILE)
with open(os.path.join(DATA, FILE)) as f:
    S = float(f.readline().split('closed at ')[1].split(' ')[0])
NOW = dt.datetime.strptime(FILE.split('_')[2], '%Y%m%d').date(); R = 0.045
N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
Q = {(r['expiry'], r['type'], num(r['strike'])): r for r in rows}


def yrs(e, d0=NOW):
    return (dt.date(int(e[:4]), int(e[4:6]), int(e[6:])) - d0).days / 365


def bs(cp, s, k, t, v):
    d1 = (math.log(s / k) + (R + v * v / 2) * t) / (v * math.sqrt(t)); d2 = d1 - v * math.sqrt(t)
    return k * math.exp(-R * t) * N(-d2) - s * N(-d1) if cp == 'P' else s * N(d1) - k * math.exp(-R * t) * N(d2)


def smile(e):
    t = yrs(e); F = S * math.exp(R * t); pts = []
    for (ee, cp, k), r in Q.items():
        if ee != e or num(r['bid']) <= 0 or num(r['ask']) <= 0 or not 0.2 < num(r['iv']) < 3: continue
        if ((cp == 'P' and k <= F) or (cp == 'C' and k > F)) and 0.5 * S <= k <= 1.8 * S:
            pts.append((math.log(k / F), num(r['iv']), max(1.0, num(r['open_interest']))))
    A = [[0.0] * 4 for _ in range(3)]
    for x, v, w in pts:
        b = [1, x, x * x]
        for i in range(3):
            A[i][3] += w * b[i] * v
            for j in range(3): A[i][j] += w * b[i] * b[j]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(A[r][c])); A[c], A[p] = A[p], A[c]
        for r in range(3):
            if r != c:
                f = A[r][c] / A[c][c]; A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    a, b, c = (A[i][3] / A[i][i] for i in range(3))
    return lambda K: a + b * math.log(K / F) + c * math.log(K / F) ** 2


def p_below(K, e):
    t = yrs(e); iv = smile(e); h = 0.25
    return (bs('P', S, K + h, t, iv(K + h)) - bs('P', S, K - h, t, iv(K - h))) / (2 * h) * math.exp(R * t)


def mid(e, cp, k):
    r = Q[(e, cp, float(k))]; return (num(r['bid']) + num(r['ask'])) / 2


def sessions(a, b):
    # weekdays after a up to and including b
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1); n += d.weekday() < 5
    return n


EV = dt.date(2026, 11, 4)
L = [f'CRCL {S:.2f} at the {NOW:%d %b} close ({FILE})']
# liquidity: the first expiry I looked at against the one I use
for e in ('20261113', '20261120'):
    for k in (70, 80):
        r = Q[(e, 'P', float(k))]
        w = (num(r['ask']) - num(r['bid'])) / mid(e, 'P', k) * 100
        L.append(f'  {e} ${k} put: {num(r["bid"]):.2f}/{num(r["ask"]):.2f}, {w:.0f}% wide, open interest {num(r["open_interest"]):.0f}')
# event size: 6 Nov straddle and the event-day move with the ordinary days stripped out (30 Oct expiry as the base vol)
atm = lambda e: (num(Q[(e, 'C', 80.0)]['iv']) + num(Q[(e, 'P', 80.0)]['iv'])) / 2
strad = mid('20261106', 'C', 80) + mid('20261106', 'P', 80)
n6, nb = sessions(NOW, dt.date(2026, 11, 6)), sessions(NOW, dt.date(2026, 10, 30))
ev = math.sqrt(max(1e-6, atm('20261106') ** 2 * n6 / 252 - atm('20261030') ** 2 * (n6 - 1) / 252))
L.append(f'6 Nov $80 straddle ${strad:.2f} = {strad / S:.1%} of the price; event-day sd {ev:.1%}, expected move {ev * math.sqrt(2 / math.pi):.1%}')
# the spread
E = '20261120'; HI, LO = 80, 70
cost = mid(E, 'P', HI) - mid(E, 'P', LO)
nat = num(Q[(E, 'P', float(HI))]['ask']) - num(Q[(E, 'P', float(LO))]['bid'])
BE = HI - cost
pm = p_below(BE, E)
L.append(f'20 Nov ${HI}/${LO} put spread: ${cost:.2f} mid, ${nat:.2f} paying the offer, break-even ${BE:.2f} ({BE / S - 1:+.1%})')
L.append(f'  market odds CRCL finishes below ${BE:.2f}: {pm:.1%}; below ${LO}: {p_below(LO, E):.1%}')
# after the report the event is gone from the vol: take it out of the 20 Nov ATM vol (17 sessions from 28 Oct)
iv20 = smile(E)
n20 = sessions(NOW, dt.date(2026, 11, 20))
base = math.sqrt((iv20(S) ** 2 * n20 / 252 - ev ** 2) / ((n20 - 1) / 252))
t_after = yrs(E, dt.date(2026, 11, 4))
L.append(f'  20 Nov ATM vol {iv20(S):.1%}; with the event taken out {base:.1%}')
for name, mv in (('down 15%', -0.15), ('flat', 0.0), ('up 15%', 0.15)):
    s1 = S * (1 + mv); sh = base - iv20(S)
    val = bs('P', s1, HI, t_after, iv20(HI) + sh) - bs('P', s1, LO, t_after, iv20(LO) + sh)
    L.append(f'  marked at the 4 Nov close, CRCL {name} ({s1:.2f}): spread worth ${val:.2f} ({val / cost - 1:+.0%})')
# my odds: even chance most ARC revenue lands in Q3; reaction odds by branch from the five reports
TREE = {'ARC in Q3': (0.5, {'up': 0.45, 'flat': 0.35, 'down': 0.20}), 'ARC in Q4': (0.5, {'up': 0.15, 'flat': 0.35, 'down': 0.50})}
MOVE = {'up': 0.15, 'flat': 0.0, 'down': -0.12}
P = {k: sum(w * br[k] for w, br in TREE.values()) for k in MOVE}
sd = base * math.sqrt(sessions(EV, dt.date(2026, 11, 20)) / 252)   # sessions from the 4 Nov close to expiry
random.seed(7); n = 200000; below = pay = 0
for _ in range(n):
    u = random.random(); c = 0
    for k in MOVE:
        c += P[k]
        if u <= c: break
    st = S * (1 + MOVE[k]) * math.exp(-sd * sd / 2 + sd * random.gauss(0, 1))
    below += st < BE; pay += min(HI - LO, max(0.0, HI - st))
L.append(f'My tree: up 15% {P["up"]:.0%}, flat {P["flat"]:.0%}, down 12% {P["down"]:.0%} on the day; then {base:.0%} vol for {sessions(EV, dt.date(2026, 11, 20))} sessions')
L.append(f'  my odds below ${BE:.2f}: {below / n:.1%}; my expected value ${pay / n:.2f} against ${cost:.2f} mid and ${nat:.2f} paying the offer')
L.append('  ' + ('no edge: I do not hold a position into the report' if pay / n < cost else 'my odds beat the price'))
# the post-report setup, indicative only (flat vol, no skew)
s1 = S * 1.15
L.append(f'Indicative, after a 15% rally: Dec $90/$80 put spread at CRCL {s1:.2f}, {base:.0%} vol: ${bs("P", s1, 90, 44 / 365, base) - bs("P", s1, 80, 44 / 365, base):.2f}')
save('option_odds.txt', '\n'.join(L) + '\n')
