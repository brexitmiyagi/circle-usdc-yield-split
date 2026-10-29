# Cross-check on the target: peers' 2027 P/E (28 Oct close over Zacks's 2027 consensus) applied to MY 2027 EPS,
# so both sides of the multiple are on the same basis. This is a value today, next to valuation.py's value today.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, save

close = {r['ticker']: num(r['close']) for r in read('closes_2026-10-28.csv')}
eps = {r['ticker']: r for r in read('peer_eps_2026-10-29.csv')}
mine = {r['Period']: r for r in read('table_vs_consensus.csv', folder='results')}
e27 = num(mine['FY27']['My GAAP EPS'])
L = [f'My 2027 GAAP EPS ${e27:.2f}; CRCL ${close["CRCL"]:.2f} = {close["CRCL"] / e27:.1f} times it']
pes = []
for t in ('V', 'MA', 'HOOD', 'COIN', 'PYPL'):
    pe = close[t] / num(eps[t]['eps']); pes.append(pe)
    L.append(f'  {t}: ${close[t]:.2f} / ${num(eps[t]["eps"]):.2f} ({eps[t]["fiscal_end"]}, {eps[t]["estimates"]} estimates) = {pe:.1f}x -> Circle ${pe * e27:.2f}')
med = sorted(pes)[len(pes) // 2]
L.append(f'  five-peer median {med:.1f}x -> ${med * e27:.2f}')
save('peer_multiples.txt', '\n'.join(L) + '\n')
