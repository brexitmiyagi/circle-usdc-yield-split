# Where USDC stands against the other dollar stablecoins, from DefiLlama's circulating supply.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, save

R = {r['symbol']: r for r in read('stablecoins_competitors_2026-10-29.csv')}
D = ['2025-10-29', '2026-06-30', '2026-09-30', '2026-10-29']
tot = {d: num(R['ALL'][d]) for d in D}
L = [f'All stablecoins: ${tot[D[0]]:.1f}bn a year ago, ${tot[D[-1]]:.1f}bn now ({tot[D[-1]] / tot[D[0]] - 1:+.1%})']
for s in ('USDT', 'USDC', 'USD1', 'USDG', 'PYUSD', 'RLUSD'):
    a, z, sep = num(R[s][D[0]]), num(R[s][D[-1]]), num(R[s]['2026-09-30'])
    L.append(f'  {s} ({R[s]["issuer"]}): ${a:.2f}bn -> ${z:.2f}bn ({z / a - 1:+.1%} in a year; {z / sep - 1:+.1%} since 30 Sep); '
             f'share {a / tot[D[0]]:.1%} -> {z / tot[D[-1]]:.1%}')
small = sum(num(R[s][D[-1]]) - num(R[s][D[0]]) for s in ('USD1', 'USDG', 'PYUSD', 'RLUSD'))
L.append(f'  USD1, USDG, PYUSD and RLUSD together added ${small:.2f}bn in a year; USDC lost ${num(R["USDC"][D[0]]) - num(R["USDC"][D[-1]]):.2f}bn')
u=R['USDC']; L.append(f"  USDC end-September: ${num(u['2025-09-30']):.2f}bn in 2025, ${num(u['2026-09-30']):.2f}bn in 2026 ({num(u['2026-09-30']) / num(u['2025-09-30']) - 1:+.1%})")
save('competition.txt', '\n'.join(L) + '\n')
