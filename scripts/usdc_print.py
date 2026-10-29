# What Circle is likely to print for USDC in circulation. Circle's own quarter-end and average numbers have run close to
# DefiLlama's, but not on them; take the gap over the last quarters and put the latest DefiLlama readings through it.
import os, sys, datetime as dt, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, save

dl = {r['date']: num(r['usdc_usd']) / 1e9 for r in read('stablecoin_supply_daily.csv')}
cq = {r['quarter']: r for r in read('circle_quarterly.csv')}
QE = {'Q2-25': '2025-06-30', 'Q3-25': '2025-09-30', 'Q4-25': '2025-12-31', 'Q1-26': '2026-03-31', 'Q2-26': '2026-06-30', 'Q3-26': '2026-09-30'}
QR = {'Q3-25': ('2025-07-01', '2025-09-30'), 'Q1-26': ('2026-01-01', '2026-03-31'), 'Q2-26': ('2026-04-01', '2026-06-30'), 'Q3-26': ('2026-07-01', '2026-09-30')}
avg = lambda a, b: statistics.mean(v for k, v in dl.items() if a <= k <= b)
gap_end = {q: num(cq[q]['usdc_end_bn']) - dl[QE[q]] for q in ('Q2-25', 'Q3-25', 'Q4-25', 'Q1-26', 'Q2-26')}
gap_avg = {q: num(cq[q]['usdc_avg_bn']) - avg(*QR[q]) for q in ('Q3-25', 'Q1-26', 'Q2-26')}
L = ['Circle less DefiLlama, quarter-end ($bn): ' + ', '.join(f'{q} {g:+.2f}' for q, g in gap_end.items())]
L.append('Circle less DefiLlama, quarter average ($bn): ' + ', '.join(f'{q} {g:+.2f}' for q, g in gap_avg.items()))
e = dl[QE['Q3-26']]; ge = list(gap_end.values())
c_lo, c_hi, c_mid = e + min(ge), e + max(ge), e + statistics.mean(ge)
prev = num(cq['Q3-25']['usdc_end_bn'])
L.append(f'End-September 2026 on DefiLlama ${e:.2f}bn -> Circle likely ${c_lo:.1f}bn to ${c_hi:.1f}bn, central ${c_mid:.1f}bn; '
         f'against Circle\'s ${prev:.1f}bn a year earlier that is {c_lo / prev - 1:+.1%} to {c_hi / prev - 1:+.1%} (central {c_mid / prev - 1:+.1%})')
a = avg(*QR['Q3-26']); ga = list(gap_avg.values())
L.append(f'Q3-26 average on DefiLlama ${a:.2f}bn -> Circle likely ${a + min(ga):.1f}bn to ${a + max(ga):.1f}bn (Q2-26 ${num(cq["Q2-26"]["usdc_avg_bn"]):.1f}bn)')
comp = {r['symbol']: r for r in read('stablecoins_competitors_2026-10-29.csv')}
now, yr = num(comp['USDC']['2026-10-29']), num(comp['USDC']['2025-10-29'])
L.append(f'Latest on DefiLlama: ${now:.2f}bn on 29 Oct 2026, {now / yr - 1:+.1%} on a year earlier and {now / e - 1:+.1%} since end-September')
save('usdc_print.txt', '\n'.join(L) + '\n')
