# What Coinbase's Q3-26 report says about Circle's Q3, and the model rerun on it.
# Circle's payment to Coinbase has run close to, but not exactly on, Coinbase's own USDC revenue (timing and definitions).
# I take the gap over the last four quarters, put Coinbase's Q3 figure through it, hold what Circle pays everyone else at
# its Q2 share of reserve income, and get the keep. Then model.py and valuation.py run again with that keep, into
# results/after_coinbase/, so the pre-report results stay as they were.
import os, sys, glob, shutil, runpy, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common
from common import read, num

cb = {r['quarter']: r for r in read('coinbase_usdc.csv')}
cq = {r['quarter']: r for r in read('circle_quarterly.csv')}
rev = lambda q: num(cb[q]['rev_products_musd']) + num(cb[q]['rev_off_platform_musd'])
circle_paid = {'Q3-25': num(cq['Q3-25']['distribution_costs_to_coinbase_musd']),
               'Q4-25': 1362.9 - 989.1,      # 10-K FY25 $1,362.9m less nine months $989.1m (10-Q Q3-25)
               'Q1-26': num(cq['Q1-26']['distribution_costs_to_coinbase_musd']),
               'Q2-26': num(cq['Q2-26']['distribution_costs_to_coinbase_musd'])}
gaps = {q: circle_paid[q] - rev(q) for q in circle_paid}
L = ['Circle paid Coinbase minus Coinbase USDC revenue: ' + ', '.join(f'{q} {g:+.1f}' for q, g in gaps.items())]
r3 = rev('Q3-26'); lo, hi = r3 + min(gaps.values()), r3 + max(gaps.values()); mid = r3 + sum(gaps.values()) / len(gaps)
L.append(f"Coinbase Q3-26 USDC revenue ${r3:.0f}m (products ${num(cb['Q3-26']['rev_products_musd']):.0f}m incl. corporate ${num(cb['Q3-26']['rev_corporate_musd']):.0f}m, off-platform ${num(cb['Q3-26']['rev_off_platform_musd']):.0f}m)")
L.append(f'Implied Circle payment to Coinbase, Q3-26: ${lo:.1f}m to ${hi:.1f}m, central ${mid:.1f}m')
# products revenue without Coinbase's own corporate USDC
ex = lambda q: num(cb[q]['rev_products_musd']) - num(cb[q]['rev_corporate_musd'])
L.append(f"Revenue on customer USDC in Coinbase products: Q2 ${ex('Q2-26'):.0f}m, Q3 ${ex('Q3-26'):.0f}m ({ex('Q3-26') - ex('Q2-26'):+.0f}m)")
# bridge of Coinbase's total USDC revenue, Q2 to Q3
hl = {r['item']: num(r['value']) for r in read('hyperliquid_q3.csv', folder='results')}
d_hl = hl['q3_coinbase_payment_change_high']
d_corp = num(cb['Q3-26']['rev_corporate_musd']) - num(cb['Q2-26']['rev_corporate_musd'])
d_off = num(cb['Q3-26']['rev_off_platform_musd']) - num(cb['Q2-26']['rev_off_platform_musd'])
d_rest = (ex('Q3-26') - ex('Q2-26')) - d_hl
L.append(f"Bridge: Q2 ${rev('Q2-26'):.0f}m {d_hl:+.1f} Hyperliquid (contract arithmetic at Q3's return) {d_rest:+.1f} other customer balances and rates "
         f"{d_corp:+.0f} Coinbase's corporate USDC {d_off:+.0f} off-platform = Q3 ${rev('Q2-26') + d_hl + d_rest + d_corp + d_off:.0f}m")
# keep: Circle's Q3 reserve income (pre-registered central) less the implied Coinbase payment less everyone else at Q2's share
ri_lo, ri_mid, ri_hi = 643.0, 656.0, 669.0          # reserve_yield.py, written down before the report
q2 = cq['Q2-26']; other_share = (num(q2['distribution_transaction_costs_musd']) - num(q2['distribution_costs_to_coinbase_musd'])) / num(q2['reserve_income_musd'])
keep = lambda ri, pay: 1 - pay / ri - other_share
k_mid = keep(ri_mid, mid)
L.append(f'Everyone else at Q2\'s {other_share:.1%} of reserve income -> keep {k_mid:.1%} central; range {keep(ri_lo, hi):.1%} to {keep(ri_hi, lo):.1%}')
# rerun the model and valuation with that keep, into a separate folder
out = os.path.join(HERE, '..', 'results', 'after_coinbase'); os.makedirs(out, exist_ok=True)
for f in glob.glob(os.path.join(HERE, '..', 'results', '*.csv')): shutil.copy(f, out)
common.RESULTS = out
os.environ['KEEP_OVERRIDE_PCT'] = f'{k_mid * 100:.2f}'
with contextlib.redirect_stdout(io.StringIO()):
    runpy.run_path(os.path.join(HERE, 'model.py'), run_name='__main__')
    runpy.run_path(os.path.join(HERE, 'valuation.py'), run_name='__main__')
    runpy.run_path(os.path.join(HERE, 'rates_float_grid.py'), run_name='__main__')
    runpy.run_path(os.path.join(HERE, 'peer_multiples.py'), run_name='__main__')
del os.environ['KEEP_OVERRIDE_PCT']
t = {r['Period']: r for r in read('table_vs_consensus.csv', folder='results')}   # common.RESULTS now points at out
li = {r['$m unless stated']: r for r in read('table_line_items.csv', folder='results')}
vs = {r['item']: num(r['value']) for r in read('valuation_summary.csv', folder='results')}
for p in ('Q3-26', 'Q4-26', 'FY26', 'FY27'):
    L.append(f"{p}: GAAP EPS ${num(t[p]['My GAAP EPS']):.2f}, without ARC ${num(t[p]['My EPS ex-ARC']):.2f}, keep {t[p]['My keep (%)']}%")
L.append(f"Q3-26 reported margin {li['RLDC margin']['Q3-26 mine']}, Q4-26 {li['RLDC margin']['Q4-26 mine']}; Q3 distribution and transaction costs ${li['Distribution and transaction costs']['Q3-26 mine']}m")
L.append(f"Value today ${vs['value_today']:.2f}, 12-month target ${vs['price_target']:.2f}; options cross-check target ${vs['options_target']:.2f}")
L.append(f"Hold range (target within 15% of the price): ${vs['price_target'] / 1.15:.2f} to ${vs['price_target'] / 0.85:.2f}")
for line in open(os.path.join(out, 'model.txt')):
    if 'Q4-26 walk' in line or 'Two assumptions close it' in line: L.append(line.rstrip())
L += [l.rstrip() for l in open(os.path.join(out, 'peer_multiples.txt'))]
g = [l.split(',') for l in open(os.path.join(out, 'rates_float_grid.csv')).read().splitlines()[1:]]
base = [float(r[4]) for r in g if float(r[0]) > 0]
col = lambda i: [float(r[i]) for r in g if float(r[0]) > 0 and float(r[1]) == 0.0][0]
L.append(f"With the drag, at the base float the target runs ${min(base):.2f} to ${max(base):.2f} across the Fed paths; on the curve, -10% float ${col(3):.2f}, base ${col(4):.2f}, +10% ${col(5):.2f}")
common.RESULTS = os.path.join(HERE, '..', 'results')
common.save('after_coinbase.txt', '\n'.join(L) + '\n')
