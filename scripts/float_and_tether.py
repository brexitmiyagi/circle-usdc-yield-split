# The float side of the story: how USDC's supply has moved, against USDT and the whole market,
# and how much of each dollar of float Circle keeps next to Tether.
import datetime as dt
from common import read, num, save

daily = read('stablecoin_supply_daily.csv')
hist = read('usdc_supply_history.csv')
last = daily[-1]
d_last = dt.date.fromisoformat(last['date'])
lines = []

def on(rows, day, col):
    for r in rows:
        if r['date'] == day.isoformat():
            return num(r[col])

# Peak and where it is now
peak = max(daily, key=lambda r: num(r['usdc_usd']))
lines.append(f"USDC peak {num(peak['usdc_usd'])/1e9:.2f}bn on {peak['date']}; {num(last['usdc_usd'])/1e9:.2f}bn on {last['date']} ({num(last['usdc_usd'])/num(peak['usdc_usd'])-1:+.1%} from peak)")
allpeak = max(daily, key=lambda r: num(r['all_stablecoins_usd']))
lines.append(f"All stablecoins peak {num(allpeak['all_stablecoins_usd'])/1e9:.1f}bn on {allpeak['date']}; {num(last['all_stablecoins_usd'])/1e9:.1f}bn on {last['date']}")

# Share of the market, Q2-26 average vs today
q2 = [r for r in daily if '2026-04-01' <= r['date'] <= '2026-06-30']
share_q2 = sum(num(r['usdc_usd']) for r in q2) / sum(num(r['all_stablecoins_usd']) for r in q2)
lines.append(f"USDC share of all stablecoins: Q2-26 average {share_q2:.1%}, now {num(last['usdc_usd'])/num(last['all_stablecoins_usd']):.1%}")

# One month, USDC against USDT
m1 = d_last - dt.timedelta(days=30)
for col, name in (('usdc_usd', 'USDC'), ('usdt_usd', 'USDT')):
    lines.append(f"{name} change over 30 days to {last['date']}: {num(last[col])/on(daily, m1, col)-1:+.1%}")

# Longer history
y1 = d_last.replace(year=d_last.year - 1)
y5 = d_last.replace(year=d_last.year - 5)
now = num(last['usdc_usd'])
v1, v5 = on(hist, y1, 'usdc_usd'), on(hist, y5, 'usdc_usd')
lines.append(f"USDC 12 months ago {v1/1e9:.1f}bn -> {now/1e9:.1f}bn ({now/v1-1:+.1%})")
lines.append(f"USDC 5 years ago {v5/1e9:.1f}bn -> {now/1e9:.1f}bn, {((now/v5)**(1/5)-1):.1%} a year")
h23 = [r for r in hist if r['date'].startswith('2023') or r['date'].startswith('2024')]
low = min(h23, key=lambda r: num(r['usdc_usd']))
lines.append(f"Low after the 2023 bank failures: {num(low['usdc_usd'])/1e9:.1f}bn on {low['date']}")

# Circle against Tether, per dollar of float, Q2-26
t = {r['item']: num(r['value']) for r in read('tether_q2_2026.csv')}
c = {r['quarter']: r for r in read('circle_quarterly.csv')}['Q2-26']
days, avg = num(c['days']), num(c['usdc_avg_bn']) * 1000
ri, dc = num(c['reserve_income_musd']), num(c['distribution_transaction_costs_musd'])
adj = {r['item']: num(r['value']) for r in read('market.csv')}['adj_ebitda_q2_musd']
lines.append(f"Tether Q2-26 net operating profit ${t['net_operating_profit_q2_musd']:.0f}m on ${t['total_liabilities_musd']/1000:.2f}bn of liabilities: {t['net_operating_profit_q2_musd']*4/t['total_liabilities_musd']:.2%} of float a year (before marks on bitcoin and gold)")
lines.append(f"Circle Q2-26 reserve income less distribution costs: {(ri-dc)*365/days/avg:.2%} of float a year; adjusted EBITDA {adj*365/days/avg:.2%}")
save('float_and_tether.txt', '\n'.join(lines) + '\n')
