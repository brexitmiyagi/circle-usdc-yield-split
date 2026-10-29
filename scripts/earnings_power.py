# What Circle earns at today's float and today's yield, counted the way an owner would:
# stock pay is a cost, the ARC token presale is left out (it is a one-off), corporate cash earns interest.
# Two keep rates: what Circle kept in Q2-26, and what it keeps once the Hyperliquid move is in (hyperliquid_q3.py).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, market, save

m = market()
circle = {r['quarter']: r for r in read('circle_quarterly.csv')}
crf = {r['month_end'][:7]: r for r in read('circle_reserve_fund_nmfp3.csv')}
supply = read('stablecoin_supply_daily.csv')

FUND_GAP = 0.08          # fund yield minus Circle's reserve return, Q1-26/Q2-26 average (reserve_yield.py)
TAX = 0.21               # US statutory; Circle's booked tax is distorted by past losses
SHARES = m['diluted_weighted_shares_q2'] / 1e6
OPEX = (m['adj_opex_guide_low_musd'] + m['adj_opex_guide_high_musd']) / 2
SBC = m['sbc_q2_musd'] * 4
DA = m['da_q2_musd'] * 4
CASH = m['corporate_cash_musd']
OTHER = (num(circle['Q1-26']['other_revenue_musd']) + num(circle['Q2-26']['other_revenue_musd'])) * 2  # H1 run-rate, no ARC
q2 = circle['Q2-26']
KEEP_Q2 = (num(q2['reserve_income_musd']) - num(q2['distribution_transaction_costs_musd'])) / num(q2['reserve_income_musd'])
KEEP_AFTER = 0.35        # middle of the 33.9% to 35.6% range in hyperliquid_q3.py
# Circle's own disclosure: +100bp adds $737m of reserve income and $360m of distribution costs.
MARG = 1 - m['rate_sens_distribution_cost_per_100bp_musd'] / m['rate_sens_reserve_income_per_100bp_musd']

def eps(float_bn, rr_pct, keep, base_rr=None):
    if base_rr is None: base_rr = rr_pct
    kept = float_bn * (base_rr * keep + (rr_pct - base_rr) * MARG) / 100 * 1000
    ebitda = kept + OTHER - OPEX
    pretax = ebitda - SBC - DA + CASH * rr_pct / 100
    return pretax * (1 - TAX) / SHARES, ebitda

float_now = float(supply[-1]['usdc_usd']) / 1e9
rr_now = float(crf['2026-09']['net_7day_yield_month_end_pct']) - FUND_GAP
L = [f'Inputs: float {float_now:.2f}bn ({supply[-1]["date"]}), reserve return {rr_now:.2f}% (fund 30 Sep less {FUND_GAP}pt), '
     f'recurring other revenue ${OTHER:.0f}m (H1-26 x2, no ARC), adj opex ${OPEX:.1f}m, stock pay ${SBC:.0f}m, D&A ${DA:.0f}m, '
     f'diluted shares {SHARES:.1f}m, tax {TAX:.0%}']
for k, label in ((KEEP_Q2, 'Q2-26 keep'), (KEEP_AFTER, 'keep after Hyperliquid')):
    e, eb = eps(float_now, rr_now, k)
    L.append(f'{label} {k:.1%}: adj EBITDA ${eb:.0f}m, owner EPS ${e:.2f}, {m["crcl_price"] / e:.0f}x at ${m["crcl_price"]:.2f}')
e0 = eps(float_now, rr_now, KEEP_AFTER)[0]
L.append(f'Q2-26 adj EBITDA x4 = ${m["adj_ebitda_q2_musd"] * 4:.0f}m (check)')
L.append(f'Per year of owner EPS at the post-Hyperliquid keep: +$10bn of USDC {eps(float_now + 10, rr_now, KEEP_AFTER)[0] - e0:+.2f}; '
         f'+25bp of yield {eps(float_now, rr_now + 0.25, KEEP_AFTER, rr_now)[0] - e0:+.2f} (Circle keeps {MARG:.1%} of a yield change); '
         f'+1pt of keep {eps(float_now, rr_now, KEEP_AFTER + 0.01)[0] - e0:+.2f}')
L.append(f'Street: Q3 revenue ${m["consensus_q3_revenue_musd"]:.1f}m, Q3 EPS ${m["consensus_q3_eps"]}, FY27 EPS ${m["consensus_fy27_eps"]}, mean target ${m["street_mean_target"]:.0f}')
if __name__ == '__main__':
    save('earnings_power.txt', '\n'.join(L) + '\n')
