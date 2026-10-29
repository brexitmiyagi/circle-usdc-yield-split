# Splits every dollar of USDC reserve income into four buckets each quarter:
# Coinbase's own platform, Circle's own platform, the shared pool, and what Circle keeps.
# The order of deductions comes from the Coinbase Collaboration Agreement (Circle 10-K FY25, Ex 10.1):
# payment base, less cost of capital, less shortfalls, less Circle's issuer retention,
# less each party's own-platform share, less approved ecosystem partners, then Coinbase takes 50%.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

circle = {r['quarter']: r for r in read('circle_quarterly.csv')}
cb = {r['quarter']: r for r in read('coinbase_usdc.csv')}

# Q4-25 gaps in Circle's quarterly disclosure, filled from the 10-K full-year numbers (marked derived):
# FY25 average USDC 64.870bn and FY25 on-platform average 11.1% (daily weighted).
days = {'Q1-25': 90, 'Q2-25': 91, 'Q3-25': 92, 'Q4-25': 92}
avg = {'Q1-25': 54.136, 'Q2-25': 61.039, 'Q3-25': 67.842}
q4_avg = (64.870 * 365 - sum(avg[q] * days[q] for q in avg)) / 92
w = {q: avg[q] * days[q] for q in avg}; w['Q4-25'] = q4_avg * 92
onp = {'Q1-25': 5.7, 'Q2-25': 7.4, 'Q3-25': 13.5}
q4_onp = (11.1 * sum(w.values()) - sum(onp[q] * w[q] for q in onp)) / w['Q4-25']

rows = ['quarter,reserve_income_m,coinbase_bucket_pct,circle_bucket_pct,shared_pool_pct,coinbase_take_of_shared_pct,'
        'circle_keep_of_reserve_income_pct,deductions_before_split_bp_of_float,circle_keep_shared_pct']
lines = []
for q in ['Q2-25', 'Q3-25', 'Q4-25', 'Q1-26', 'Q2-26']:
    ri = num(circle[q]['reserve_income_musd'])
    dc = num(circle[q]['distribution_transaction_costs_musd'])
    c = cb[q]
    cb_bal = float(c['usdc_in_coinbase_products_bn'])  # corporate balances sit inside this
    tot = float(c['usdc_avg_mktcap_bn'])
    cb_pct = cb_bal / tot * 100
    ci_pct = num(circle[q]['circle_on_platform_pct']) if circle[q]['circle_on_platform_pct'] else q4_onp
    sh_pct = 100 - cb_pct - ci_pct
    cb_onplat = float(c['rev_products_musd'])
    cb_off = float(c['rev_off_platform_musd'])
    shared_gross = ri * sh_pct / 100
    circle_own = ri * ci_pct / 100
    # residual after ecosystem partners = 2 x Coinbase's off-platform take
    deductions = ri - cb_onplat - circle_own - 2 * cb_off
    favg = num(circle[q]['usdc_avg_bn']) if circle[q]['usdc_avg_bn'] else q4_avg
    dq = num(circle[q]['days']) if circle[q]['days'] else 92
    bp = deductions / 1000 * 365 / dq / favg * 1e4
    keep = (ri - dc) / ri * 100
    keep_shared = (shared_gross - cb_off) / shared_gross * 100
    rows.append(f'{q},{ri:.1f},{cb_pct:.1f},{ci_pct:.1f},{sh_pct:.1f},{cb_off / shared_gross * 100:.1f},{keep:.1f},{bp:.0f},{keep_shared:.1f}')
    lines.append(f'{q}: Coinbase bucket {cb_pct:.1f}%, Circle bucket {ci_pct:.1f}%, shared {sh_pct:.1f}% | '
                 f'Coinbase gets {cb_off / shared_gross * 100:.1f}% of shared-pool yield | Circle keeps {keep:.1f}% of all reserve income | '
                 f'deductions before the 50/50 split ~{bp:.0f}bp of float a year')
lines.append(f'(Q4-25 average USDC {q4_avg:.2f}bn and Circle on-platform {q4_onp:.1f}% are derived from 10-K full-year figures)')

# What moving USDC out of the shared pool and onto Circle's platform is worth
q2 = circle['Q2-26']; y = num(q2['reserve_return_pct']) / 100
moved = (19.5 - 7.4) / 100 * num(q2['usdc_avg_bn'])
lines.append(f'Circle bucket grew from 7.4% to 19.5% of float in a year: about ${moved:.1f}bn moved onto Circle\'s platform.')
cb_q2 = float(cb['Q2-26']['rev_off_platform_musd']) / (num(q2['reserve_income_musd']) * float(rows[-1].split(',')[4]) / 100)
lines.append(f'At a {y * 100:.2f}% reserve return, the {cb_q2 * 100:.0f}% of shared-pool yield Coinbase took in Q2-26 is worth about '
             f'${moved * y * cb_q2 * 1000:.0f}m a year on that float, before any incentives Circle pays to attract it.')
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'yield_split.csv'), 'w') as f:
    f.write('\n'.join(rows) + '\n')
save('yield_split.txt', '\n'.join(lines))
