# Writes the CSVs behind each chart in the post, so the Datawrapper charts can be rebuilt from here.
import os, sys, csv, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, RESULTS

def write(name, header, rows):
    with open(os.path.join(RESULTS, name), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print('wrote', name, len(rows), 'rows')

split = list(csv.DictReader(open(os.path.join(RESULTS, 'yield_split.csv'))))
write('chart1_three_buckets.csv', ['Quarter', "Coinbase's platform", "Circle's platform", 'Shared pool'],
      [[r['quarter'], r['coinbase_bucket_pct'], r['circle_bucket_pct'], r['shared_pool_pct']] for r in split])

# chart 2: where each dollar of Q2-26 reserve income went (from the release and both companies' filings)
c = {r['quarter']: r for r in read('circle_quarterly.csv')}['Q2-26']
cb = {r['quarter']: r for r in read('coinbase_usdc.csv')}['Q2-26']
ri = float(c['reserve_income_musd']); dc = float(c['distribution_transaction_costs_musd'])
to_cb = float(c['distribution_costs_to_coinbase_musd'])
cb_prod = float(cb['rev_products_musd']); cb_off = to_cb - cb_prod
write('chart2_q2_dollar.csv', ['Where it went', 'USD m', 'Cents per dollar'],
      [["Coinbase, USDC on its own platform", round(cb_prod, 1), round(cb_prod / ri * 100, 1)],
       ["Coinbase, its half of the shared pool", round(cb_off, 1), round(cb_off / ri * 100, 1)],
       ['Other distributors and transaction costs', round(dc - to_cb, 1), round((dc - to_cb) / ri * 100, 1)],
       ['Kept by Circle', round(ri - dc, 1), round((ri - dc) / ri * 100, 1)]])

sup = read('stablecoin_supply_daily.csv')
yc = {}
for f in ['treasury_par_yield_curve_2025.csv', 'treasury_par_yield_curve_2026.csv']:
    for r in read(f):
        m, d, y = r['Date'].split('/'); yc[f'{y}-{m}-{d}'] = r['3 Mo']
rows = [[r['date'], round(float(r['usdc_usd']) / 1e9, 2), yc.get(r['date'], '')] for r in sup if r['date'] >= '2025-06-01']
write('chart3_usdc_vs_3m_bill.csv', ['Date', 'USDC supply ($bn, DefiLlama)', '3-month T-bill (%)'], rows)

write('chart4_reserve_fund.csv', ['Month end', 'Net 7-day yield, monthly avg (%)', 'Net 7-day yield, month end (%)', 'Repo share of fund (%)', 'WAM (days)'],
      [[r['month_end'], r['net_7day_yield_avg_pct'], r['net_7day_yield_month_end_pct'], r['repo_share_pct'], r['wam_days']] for r in read('circle_reserve_fund_nmfp3.csv')])
