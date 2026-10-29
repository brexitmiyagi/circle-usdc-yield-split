# Checks that the numbers I lean on agree with each other across two different sources.
# Fails loudly if something does not tie.
import os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

out = []
circle = {r['quarter']: r for r in read('circle_quarterly.csv')}
cb = {r['quarter']: r for r in read('coinbase_usdc.csv')}
supply = read('stablecoin_supply_daily.csv')

def llama_avg(a, b):
    v = [float(r['usdc_usd']) for r in supply if a <= r['date'] <= b]
    return st.mean(v) / 1e9

# 1. Circle's own average USDC vs DefiLlama's daily supply (independent, onchain)
for q, a, b in [('Q2-25', '2025-04-01', '2025-06-30'), ('Q3-25', '2025-07-01', '2025-09-30'),
                ('Q1-26', '2026-01-01', '2026-03-31'), ('Q2-26', '2026-04-01', '2026-06-30')]:
    c = num(circle[q]['usdc_avg_bn']); l = llama_avg(a, b)
    gap = (l / c - 1) * 100
    out.append(f'{q} USDC average: Circle {c:.2f}bn, DefiLlama {l:.2f}bn, gap {gap:+.2f}%')
    assert abs(gap) < 1.5, q

# 2. What Circle says it paid Coinbase vs what Coinbase says it earned from USDC (two filers)
for q in ['Q2-25', 'Q1-26', 'Q2-26']:
    paid = num(circle[q]['distribution_costs_to_coinbase_musd'])
    got = float(cb[q]['rev_products_musd']) + float(cb[q]['rev_off_platform_musd'])  # corporate is inside products
    gap = (got / paid - 1) * 100
    out.append(f'{q} Circle paid Coinbase {paid:.1f}m, Coinbase reports {got:.0f}m from USDC, gap {gap:+.1f}%')
    assert abs(gap) < 3, q

# 3. Reserve return rate: reserve income x 365/days / average USDC should match Circle's printed rate
for q in ['Q2-25', 'Q1-26', 'Q2-26']:
    r = circle[q]
    calc = num(r['reserve_income_musd']) / 1000 * 365 / num(r['days']) / num(r['usdc_avg_bn']) * 100
    out.append(f'{q} reserve return: printed {r["reserve_return_pct"]}%, rebuilt {calc:.2f}%')
    assert abs(calc - num(r['reserve_return_pct'])) < 0.1, q

# 4. Q2-26 revenue less distribution costs ties to the release ($289m, 41%)
r = circle['Q2-26']
tot = num(r['reserve_income_musd']) + num(r['other_revenue_musd'])
rldc = tot - num(r['distribution_transaction_costs_musd']) - num(r['other_costs_musd'])
out.append(f'Q2-26 total revenue {tot:.1f}m, RLDC {rldc:.1f}m, margin {rldc / tot * 100:.1f}%')
assert abs(rldc - 289) < 1 and abs(tot - 701.3) < 0.1

out.append('ALL TIE-OUTS PASS')
save('tieout.txt', '\n'.join(out))
