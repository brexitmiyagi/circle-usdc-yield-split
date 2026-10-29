# The Hyperliquid move, measured, and what it does to Circle's third quarter.
# Since June, Hyperliquid's native USDC is backed on HyperEVM by two addresses kept at a fixed 9:1 split every block:
# Coinbase's AQA treasury (Coinbase's platform) and Circle's CoreDepositWallet (Circle's platform). USDC still in the
# legacy Arbitrum bridge sits in neither, so it is shared-pool USDC under the Coinbase contract.
# Under that contract USDC on Coinbase's platform earns Coinbase the full yield, USDC on Circle's platform earns Circle
# the full yield, and Circle keeps only part of a shared-pool dollar.
import os, sys, datetime as dt, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

L = []
# Measured: daily HyperEVM balances of the two backing addresses (archive RPC, cross-checked on a second archive RPC)
oc = {dt.date.fromisoformat(r['date']): r for r in read('hyperliquid_split_onchain_daily.csv')}
tre = {k: num(v['treasury_usdc']) / 1e9 for k, v in oc.items()}
cdw = {k: num(v['circle_linked_usdc']) / 1e9 for k, v in oc.items()}
start = min(k for k, v in tre.items() if v > 0)
last = max(oc)
L.append(f"Split starts {start}: before it, all native Hyperliquid USDC sat in Circle's Core Deposit Wallet (${cdw[start - dt.timedelta(days=1)]:.2f}bn on {start - dt.timedelta(days=1)}); "
         f"on {start} Coinbase's treasury held ${tre[start]:.2f}bn and Circle's wallet ${cdw[start]:.2f}bn")
L.append(f"Latest {last}: Coinbase ${tre[last]:.3f}bn, Circle ${cdw[last]:.3f}bn, Coinbase share {tre[last] / (tre[last] + cdw[last]):.2%}")
hb = {dt.date.fromisoformat(r['date']): r for r in read('hyperliquid_bridge_defillama.csv')}
arb = {k: num(v['arbitrum_bridge_usd']) / 1e9 for k, v in hb.items()}
def mean(s, a, b): return statistics.mean(v for k, v in s.items() if a <= k <= b)
Q2a, Q2b, Q3a, Q3b = dt.date(2026, 4, 1), dt.date(2026, 6, 30), dt.date(2026, 7, 1), dt.date(2026, 9, 30)
t2, c2, a2 = mean(tre, Q2a, Q2b), mean(cdw, Q2a, Q2b), mean(arb, Q2a, Q2b)
t3, c3, a3 = mean(tre, Q3a, Q3b), mean(cdw, Q3a, Q3b), mean(arb, Q3a, Q3b)
L.append(f"Quarterly averages ($bn): Coinbase treasury Q2 {t2:.3f}, Q3 {t3:.3f}; Circle wallet Q2 {c2:.3f}, Q3 {c3:.3f}; legacy Arbitrum bridge (DefiLlama) Q2 {a2:.3f}, Q3 {a3:.3f}")

ys = {r['quarter']: r for r in read('yield_split.csv', folder='results')}
q = {r['quarter']: r for r in read('circle_quarterly.csv')}
y = 3.55 / 100               # pre-registered Q3 reserve return (reserve_yield.py)
cb_take = num(ys['Q2-26']['coinbase_take_of_shared_pct']) / 100
ded = num(ys['Q2-26']['deductions_before_split_bp_of_float']) / 1e4
s_hi, s_lo = y * (1 - cb_take), 0.5 * (y - ded)   # Circle's take on a shared-pool dollar, a year
ri3 = 656.0                                       # pre-registered Q3 reserve income (reserve_yield.py)
f = 92 / 365 * 1000
out = []
for s, sl in ((s_lo, 'low'), (s_hi, 'high')):
    keep2 = (c2 * y + a2 * s) * f; keep3 = (c3 * y + a3 * s) * f
    pay2 = (t2 * y + a2 * cb_take * y) * f; pay3 = (t3 * y + a3 * cb_take * y) * f
    out.append((keep3 - keep2, pay3 - pay2))
    L.append(f"  Circle's shared-pool take {sl} ({s:.2%}): on Hyperliquid's USDC Circle keeps ${keep2:.1f}m on Q2's mix and ${keep3:.1f}m on Q3's ({keep3 - keep2:+.1f}m); "
             f"Circle pays Coinbase ${pay2:.1f}m and ${pay3:.1f}m ({pay3 - pay2:+.1f}m), both at a {y:.2%} return for 92 days")
# Binance's customer USDC (proof of reserves) fell between Q2 and Q3; Circle keeps about 1.0 to 1.3 cents a year on it (distribution_history.py)
por = {dt.date.fromisoformat(r['snapshot']): num(r['customer_liability_musd']) / 1000 for r in read('binance_por_usdc.csv')}
def trap(a, b):
    pts = [por[k] for k in sorted(por) if a <= k <= b]
    return (pts[0] / 2 + sum(pts[1:-1]) + pts[-1] / 2) / (len(pts) - 1)
db = trap(dt.date(2026, 7, 1), dt.date(2026, 10, 1)) - trap(dt.date(2026, 4, 1), dt.date(2026, 7, 1))
bin_lo, bin_hi = db * 0.0134 * f, db * 0.0100 * f
L.append(f"Binance customers' USDC Q3 vs Q2: {db:+.2f}bn -> Circle keeps ${bin_lo:+.1f}m to ${bin_hi:+.1f}m (if it sits on Circle's side)")
dk = [o[0] for o in out]; dp = [o[1] for o in out]
keep_q2 = (num(q['Q2-26']['reserve_income_musd']) - num(q['Q2-26']['distribution_transaction_costs_musd'])) / num(q['Q2-26']['reserve_income_musd'])
cb_share_q2 = num(q['Q2-26']['distribution_costs_to_coinbase_musd']) / num(q['Q2-26']['reserve_income_musd'])
import keep_method as km
lo_k, hi_k = km.keep_range('Q2-26', 'Q3-26', ri3, y)
BT = {r['item']: num(r['value']) for r in read('backtest_summary.csv', folder='results')}
adj = -BT['method_bias_pt'] / 100
L.append(f"Measured: Hyperliquid alone moves Circle's Q3 keep by ${min(dk):.1f}m to ${max(dk):.1f}m and its payment to Coinbase by ${min(dp):+.1f}m to ${max(dp):+.1f}m")
L.append(f"Circle's keep (keep_method.py, the backtested method): {keep_q2:.1%} in Q2 -> {lo_k:.1%} to {hi_k:.1%} in Q3, before any undisclosed Circle/Coinbase side share")
L.append(f"The method ran {adj * 100:.1f}pt low on average over the last {BT['quarters']:.0f} quarters (backtest_keep.py); corrected for that, the midpoint is {(lo_k + hi_k) / 2 + adj:.1%}")
for ri in (643.0, 656.0, 669.0):
    L.append(f"  Q3 reserve income ${ri:.0f}m: Circle's payment to Coinbase about ${cb_share_q2 * ri + min(dp):.0f}m (Q2-26: ${num(q['Q2-26']['distribution_costs_to_coinbase_musd']):.1f}m)")
# Circle's own-platform balance: Q2 average less Hyperliquid's and Binance's Q3 drops
plat2 = num(q['Q2-26']['usdc_avg_bn']) * num(q['Q2-26']['circle_on_platform_pct']) / 100
plat3 = plat2 + (c3 - c2) + db
L.append(f"Circle's own platform: Q2 average ${plat2:.2f}bn; less Hyperliquid ({c3 - c2:+.2f}bn) and Binance customers ({db:+.2f}bn) = ${plat3:.2f}bn, "
         f"{plat3 / 73.40:.1%} of the Q3 average before any other growth (19.5% in Q2)")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'hyperliquid_q3.csv'), 'w') as fh:
    fh.write('item,value\n')
    fh.write(f"q3_keep_low,{lo_k * 100:.2f}\nq3_keep_high,{hi_k * 100:.2f}\nq3_keep_mid,{(lo_k + hi_k) / 2 * 100:.2f}\nq3_keep_mid_bias_adjusted,{((lo_k + hi_k) / 2 + adj) * 100:.2f}\n")
    fh.write(f"q3_coinbase_payment_change_low,{min(dp):.2f}\nq3_coinbase_payment_change_high,{max(dp):.2f}\n")
    fh.write(f"q3_circle_platform_share_ex_growth_pct,{plat3 / 73.40 * 100:.2f}\n")
    for k, v in (('coinbase_treasury_q2_bn', t2), ('circle_wallet_q2_bn', c2), ('arbitrum_bridge_q2_bn', a2), ('coinbase_treasury_q3_bn', t3),
                 ('circle_wallet_q3_bn', c3), ('arbitrum_bridge_q3_bn', a3), ('shared_take_low_pct', s_lo * 100), ('shared_take_high_pct', s_hi * 100),
                 ('coinbase_take_of_shared_pct', cb_take * 100), ('binance_customer_usdc_change_bn', db), ('keep_q2_pct', keep_q2 * 100),
                 ('q3_reserve_income_preregistered_musd', ri3), ('q3_return_pct', y * 100)):
        fh.write(f"{k},{v:.6f}\n")

# Second path: what Circle's own guidance implies for the second half.
c = {r['item']: num(r['value']) for r in read('q2_2026_call_facts.csv')}
q1r = num(q['Q1-26']['reserve_income_musd']) + num(q['Q1-26']['other_revenue_musd'])
q2r = num(q['Q2-26']['reserve_income_musd']) + num(q['Q2-26']['other_revenue_musd'])
q1m = q1r - num(q['Q1-26']['distribution_transaction_costs_musd']) - num(q['Q1-26']['other_costs_musd'])
q2m = q2r - num(q['Q2-26']['distribution_transaction_costs_musd']) - num(q['Q2-26']['other_costs_musd'])
h1r, h1m = q1r + q2r, q1m + q2m
L.append(f"RLDC margin: Q1-26 {q1m / q1r:.1%}, Q2-26 {q2m / q2r:.1%}, H1 {h1m / h1r:.1%}")
other_h1 = num(q['Q1-26']['other_revenue_musd']) + num(q['Q2-26']['other_revenue_musd'])
res = []
for ri_h2 in (1300, 1350, 1400):
    for oth in (c['fy26_other_revenue_ex_arc_low_musd'], c['fy26_other_revenue_ex_arc_high_musd']):
        for mg in (c['fy26_rldc_margin_ex_arc_guide_low_pct'], c['fy26_rldc_margin_ex_arc_guide_high_pct']):
            h2r = ri_h2 + oth - other_h1
            res.append(((h1r + h2r) * mg / 100 - h1m) / h2r)
L.append(f"Guidance (ex-ARC full-year RLDC margin near 39%) implies H2 margin of {min(res):.1%} to {max(res):.1%} for H2 reserve income of $1.30bn to $1.40bn")
save('hyperliquid_q3.txt', '\n'.join(L) + '\n')

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'chart8_hyperliquid_usdc.csv'), 'w') as fh:
    fh.write('Date,Coinbase treasury ($bn),Circle Core Deposit Wallet ($bn),Legacy Arbitrum bridge ($bn)\n')
    for k in sorted(tre):
        fh.write(f"{k},{tre[k]:.3f},{cdw[k]:.3f},{arb.get(k, float('nan')):.3f}\n")
