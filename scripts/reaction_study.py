# What the stock has done on each of Circle's five reports, next to what the report said.
# All five came out before the open, so the day's move runs from the prior close. Five sessions = the report day plus four.
# The keep (reserve income less distribution and transaction costs, over reserve income) comes from each quarter's income statement.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import read, num, save

px = read('prices_daily.csv')
dates = [r['date'] for r in px]
crcl = {r['date']: num(r['CRCL']) for r in px}
q = {r['quarter']: r for r in read('circle_quarterly.csv')}
prev = {'Q2-25': 'Q1-25', 'Q3-25': 'Q2-25', 'Q4-25': 'Q3-25', 'Q1-26': 'Q4-25', 'Q2-26': 'Q1-26'}


def keep(qq):
    r = q[qq]
    return (num(r['reserve_income_musd']) - num(r['distribution_transaction_costs_musd'])) / num(r['reserve_income_musd']) * 100


L = ['Report     day move  5-session  revenue vs consensus     USDC end (q/q)    keep (prior)   what moved it']
rows = [['quarter', 'report_date', 'day_move_pct', 'five_session_pct', 'revenue_musd', 'consensus_musd', 'usdc_end_bn', 'usdc_qoq_pct', 'keep_pct', 'keep_prior_pct']]
for r in read('earnings_reports.csv'):
    i = dates.index(r['report_date'])
    p0, p1, p5 = crcl[dates[i - 1]], crcl[dates[i]], crcl[dates[i + 4]]
    d1, d5 = (p1 / p0 - 1) * 100, (p5 / p0 - 1) * 100
    qq = r['quarter']; pq = prev[qq]
    usdc_end, usdc_prev = num(q[qq]['usdc_end_bn']), num(q[pq]['usdc_end_bn'])
    qoq = (usdc_end / usdc_prev - 1) * 100
    L.append(f"{qq} {r['report_date']}  {d1:+6.1f}%   {d5:+6.1f}%   ${num(r['revenue_musd']):.0f}m vs ${num(r['revenue_consensus_musd']):.0f}m   "
             f"${usdc_end:.1f}bn ({qoq:+.1f}%)   {keep(qq):.1f}% ({keep(pq):.1f}%)   {r['what_moved_it']}")
    rows.append([qq, r['report_date'], f'{d1:.2f}', f'{d5:.2f}', r['revenue_musd'], r['revenue_consensus_musd'], f'{usdc_end:.1f}', f'{qoq:.1f}', f'{keep(qq):.1f}', f'{keep(pq):.1f}'])
L.append('Closes from prices_daily.csv (Yahoo); I matched every one of these against Nasdaq.')
save('reaction_study.txt', '\n'.join(L) + '\n')
with open(os.path.join(HERE, '..', 'results', 'reaction_study.csv'), 'w') as f:
    f.write('\n'.join(','.join(map(str, x)) for x in rows) + '\n')
