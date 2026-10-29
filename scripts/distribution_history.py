# Who gets Circle's reserve income, year by year, and what Binance costs per dollar of USDC it holds.
# Inputs are Circle's own filings (424B4, 10-K FY25, 10-Qs) and Binance's monthly proof-of-reserves reports.
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

lines = []
hist = read('circle_distribution_history.csv')
lines.append('Share of reserve income: Circle keeps / paid to Coinbase / paid to everyone else')
for r in hist:
    ri, dc, cb = num(r['reserve_income_musd']), num(r['distribution_transaction_costs_musd']), num(r['paid_to_coinbase_musd'])
    lines.append(f"  {r['period']}: keeps {(ri - dc) / ri:.1%} | Coinbase {cb / ri:.1%} | others ${dc - cb:.1f}m = {(dc - cb) / ri:.1%}  ({r['basis']} basis)")
q = {r['quarter']: r for r in read('circle_quarterly.csv')}
for k in ('Q2-25', 'Q2-26'):
    ri, dc, cb = num(q[k]['reserve_income_musd']), num(q[k]['distribution_transaction_costs_musd']), num(q[k]['distribution_costs_to_coinbase_musd'])
    lines.append(f"  {k}: keeps {(ri - dc) / ri:.1%} | Coinbase {cb / ri:.1%} | others ${dc - cb:.1f}m = {(dc - cb) / ri:.1%}")

# Binance's cost to Circle in 2025, bounded from the filings.
f = {r['item']: num(r['value_musd']) for r in read('binance_cost_facts.csv')}
fy24 = {r['period']: r for r in hist}['FY24']
fy24_others = num(fy24['distribution_transaction_costs_musd']) - num(fy24['paid_to_coinbase_musd'])
lo = f['binance_upfront_fee_fy24'] + f['binance_cost_increase_fy25_vs_fy24']   # FY24 Binance cost was at least the upfront fee
hi = fy24_others + f['binance_cost_increase_fy25_vs_fy24']                   # and at most everything not paid to Coinbase
lines.append(f"Binance cost to Circle in 2025: between ${lo:.1f}m and ${hi:.1f}m (FY24 Binance cost between the ${f['binance_upfront_fee_fy24']}m upfront fee and the ${fy24_others:.1f}m paid to all non-Coinbase partners, plus the ${f['binance_cost_increase_fy25_vs_fy24']}m increase)")

# Binance's own USDC, averaged over 2025 from the monthly snapshots (trapezoid between month starts).
por = {dt.date.fromisoformat(r['snapshot']): r for r in read('binance_por_usdc.csv')}
def avg(a, b, col):
    pts = [num(por[k][col]) for k in sorted(por) if a <= k <= b]
    return (pts[0] / 2 + sum(pts[1:-1]) + pts[-1] / 2) / (len(pts) - 1)
hold25 = avg(dt.date(2025, 1, 1), dt.date(2026, 1, 1), 'binance_holdings_musd')
cust25 = avg(dt.date(2025, 1, 1), dt.date(2026, 1, 1), 'customer_liability_musd')
fy25 = {r['period']: r for r in hist}['FY25']
avg_usdc25 = 64.870  # Circle 10-K FY25, average USDC in circulation
rr = num(fy25['reserve_income_musd']) / avg_usdc25 / 1000
lines.append(f"Binance's USDC in 2025 (its proof-of-reserves reports): ${hold25 / 1000:.2f}bn held on average, of which ${cust25 / 1000:.2f}bn belonged to customers")
lines.append(f"Circle's 2025 reserve return: {rr:.2%}")
lines.append(f"Binance cost per dollar of USDC Binance held: {lo / hold25:.2%} to {hi / hold25:.2%} a year, so {lo / hold25 / rr:.0%} to {hi / hold25 / rr:.0%} of what that dollar earned in reserves")
lines.append(f"What Circle keeps on a dollar Binance holds: {rr - hi / hold25:.2%} to {rr - lo / hold25:.2%} a year")
keep25 = (num(fy25['reserve_income_musd']) - num(fy25['distribution_transaction_costs_musd'])) / avg_usdc25 / 1000
lines.append(f"What Circle kept on the average dollar of USDC in 2025: {keep25:.2%} a year")
ri_q2, dc_q2 = num(q['Q2-26']['reserve_income_musd']), num(q['Q2-26']['distribution_transaction_costs_musd'])
lines.append(f"What Circle kept on the average dollar of USDC in Q2-26: {(ri_q2 - dc_q2) * 365 / 91 / num(q['Q2-26']['usdc_avg_bn']) / 1000:.2%} a year")
lines.append(f"Binance's $100m share purchase (Sep 2026) against its 2025 fees: {f['binance_private_placement_sep_2026'] / lo:.0%} to {f['binance_private_placement_sep_2026'] / hi:.0%} of one year")

# Rates moved a lot between 2024 and 2026, and Circle keeps more of each extra basis point than of the average one.
# So put H1-26 back at 2024's reserve return using Circle's own rate table (10-Q Q2-26 Item 3: +100bp = +$737m reserve
# income and +$360m distribution costs a year), and take the one-off $60.25m Binance fee out of 2024.
m = {r['item']: num(r['value']) for r in read('market.csv')}
h1 = {r['period']: r for r in hist}['H1-26']
ri_h1, dc_h1 = num(h1['reserve_income_musd']), num(h1['distribution_transaction_costs_musd'])
rr_h1 = (num(q['Q1-26']['reserve_income_musd']) + num(q['Q2-26']['reserve_income_musd'])) / (num(q['Q1-26']['usdc_avg_bn']) * 90 + num(q['Q2-26']['usdc_avg_bn']) * 91) * 365 / 1000
rr_24 = 0.050  # Circle 424B4: reserve return rate 5.0% for 2024 (average USDC $33,342m)
gap = (rr_24 - rr_h1) * 100
ri_adj = ri_h1 + gap * m['rate_sens_reserve_income_per_100bp_musd'] / 2
dc_adj = dc_h1 + gap * m['rate_sens_distribution_cost_per_100bp_musd'] / 2
ri24, dc24 = num(fy24['reserve_income_musd']), num(fy24['distribution_transaction_costs_musd'])
lines.append(f"H1-26 reserve return {rr_h1:.2%} vs 5.0% in 2024. At 2024's rate, Circle would have kept {(ri_adj - dc_adj) / ri_adj:.1%} in H1-26 (actual {(ri_h1 - dc_h1) / ri_h1:.1%})")
lines.append(f"2024 keep without the one-off Binance fee: {(ri24 - dc24 + f['binance_upfront_fee_fy24']) / ri24:.1%} (with it: {(ri24 - dc24) / ri24:.1%})")

# Was the growth since 2024 bought at a lower margin? Cents kept per dollar of float, both periods at 2024's 5.0% return.
f24 = 33.342   # Circle 424B4: average USDC in circulation 2024, $bn
f26 = (num(q['Q1-26']['usdc_avg_bn']) * 90 + num(q['Q2-26']['usdc_avg_bn']) * 91) / 181
k24 = (ri24 - dc24 + f['binance_upfront_fee_fy24']) / ri24 * rr_24
k26 = (ri_adj - dc_adj) / ri_adj * rr_24
inc = (k26 * f26 - k24 * f24) / (f26 - f24)
lines.append(f"Cents kept per dollar of float at a 5.0% return: 2024 {k24 * 100:.2f}c on ${f24:.1f}bn, H1-26 {k26 * 100:.2f}c on ${f26:.1f}bn; "
             f"the extra ${f26 - f24:.1f}bn earned {inc * 100:.2f}c, {inc / k24:.0%} of the 2024 rate")

# Chart data: who gets each dollar of reserve income
out = ['Period,Circle keeps (%),Coinbase (%),Binance and other partners (%)']
for r in hist:
    ri, dc, cb = num(r['reserve_income_musd']), num(r['distribution_transaction_costs_musd']), num(r['paid_to_coinbase_musd'])
    out.append(f"{r['period']},{(ri - dc) / ri * 100:.1f},{cb / ri * 100:.1f},{(dc - cb) / ri * 100:.1f}")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'chart6_who_gets_reserve_income.csv'), 'w') as fh:
    fh.write('\n'.join(out) + '\n')
save('distribution_history.txt', '\n'.join(lines) + '\n')
