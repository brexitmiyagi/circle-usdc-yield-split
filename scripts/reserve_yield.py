# Circle's reserve return vs the Circle Reserve Fund's own reported yield (SEC N-MFP3, monthly),
# and the pre-registered Q3-26 reserve income estimate.
import os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, save

crf = {r['month_end'][:7]: r for r in read('circle_reserve_fund_nmfp3.csv')}
circle = {r['quarter']: r for r in read('circle_quarterly.csv')}
supply = read('stablecoin_supply_daily.csv')
lines = []

def crf_q(months):
    return st.mean(float(crf[m]['net_7day_yield_avg_pct']) for m in months)

q1 = crf_q(['2026-01', '2026-02', '2026-03']); q2 = crf_q(['2026-04', '2026-05', '2026-06'])
q3 = crf_q(['2026-07', '2026-08', '2026-09'])
gap_q1 = q1 - num(circle['Q1-26']['reserve_income_musd']) / 1000 * 365 / 90 / num(circle['Q1-26']['usdc_avg_bn']) * 100
gap_q2 = q2 - num(circle['Q2-26']['reserve_income_musd']) / 1000 * 365 / 91 / num(circle['Q2-26']['usdc_avg_bn']) * 100
gap = (gap_q1 + gap_q2) / 2
lines.append(f'Circle Reserve Fund net 7-day yield, quarterly average: Q1-26 {q1:.2f}%, Q2-26 {q2:.2f}%, Q3-26 {q3:.2f}%')
lines.append(f'Fund yield minus Circle\'s rebuilt reserve return: Q1-26 {gap_q1:.2f}pt, Q2-26 {gap_q2:.2f}pt (avg {gap:.2f}pt; cash at banks earns less)')
lines.append(f'Fund net 7-day yield at 30 Sep 2026: {crf["2026-09"]["net_7day_yield_month_end_pct"]}% '
             f'(30 Jun: {crf["2026-06"]["net_7day_yield_month_end_pct"]}%); repo share of fund fell from '
             f'{crf["2026-06"]["repo_share_pct"]}% to {crf["2026-09"]["repo_share_pct"]}%, WAM {crf["2026-06"]["wam_days"]} -> {crf["2026-09"]["wam_days"]} days')

q3_avg = st.mean(float(r['usdc_usd']) for r in supply if '2026-07-01' <= r['date'] <= '2026-09-30') / 1e9
# calibrate DefiLlama to Circle's own average using Q1-26 and Q2-26
cal = []
for q, a, b in [('Q1-26', '2026-01-01', '2026-03-31'), ('Q2-26', '2026-04-01', '2026-06-30')]:
    l = st.mean(float(r['usdc_usd']) for r in supply if a <= r['date'] <= b) / 1e9
    cal.append(num(circle[q]['usdc_avg_bn']) / l)
cal = st.mean(cal)
q3_circle_avg = q3_avg * cal
rr = q3 - gap
ri = q3_circle_avg * rr / 100 * 92 / 365 * 1000
lines.append(f'Q3-26 USDC average (DefiLlama) {q3_avg:.2f}bn -> Circle basis {q3_circle_avg:.2f}bn (vs {circle["Q2-26"]["usdc_avg_bn"]}bn in Q2)')
lines.append(f'PRE-REGISTERED Q3-26: reserve return {rr:.2f}%, reserve income ${ri:.0f}m (range ${ri * 0.98:.0f}m to ${ri * 1.02:.0f}m) '
             f'vs Q2-26 ${num(circle["Q2-26"]["reserve_income_musd"]):.0f}m')
last = supply[-1]
lines.append(f'USDC on {last["date"]}: {float(last["usdc_usd"]) / 1e9:.2f}bn, {((float(last["usdc_usd"]) / 1e9) / num(circle["Q2-26"]["usdc_avg_bn"]) - 1) * 100:+.1f}% vs the Q2-26 average')
save('reserve_yield.txt', '\n'.join(lines))
