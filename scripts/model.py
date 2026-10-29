# Three-statement model: Q1-26 and Q2-26 actuals, Q3-26 to Q4-27 forecasts, FY26 and FY27 totals, against consensus.
# Base case: USDC follows the JPMorgan path from Q4-26 (less the rate drag used in valuation.py), the reserve return follows
# the Treasury forward curve less Circle's usual gap to the 3-month bill, and Circle's keep starts from the Q3-26 level
# measured on-chain (hyperliquid_q3.py, corrected for the backtest's average miss) and is held as yields move, which is what
# backtest_keep.py supports (switch use_rate_table_for_keep to 1 for Circle's 51.2% marginal rate).
# ARC token revenue: Circle books presale proceeds as milestones are met and guided ~$180m for 2026 (Q2 call). Mainnet went
# live 16 Sep 2026, so some of it may land in Q3; the Q3/Q4 split is not disclosed. The base case splits it evenly and
# the output shows Q3 at $0, $90m and $180m. The full-year total does not depend on the split.
# EPS: GAAP diluted (what the Street forecasts; includes ARC token revenue, charges stock pay) and ex-ARC.
# The balance sheet only carries the lines that move; everything else is held at 30 June 2026. Stablecoin reserves and the
# USDC liability move one for one and are shown at period-end USDC (reserves keep their $233.6m excess over the liability).
import os, sys, csv, statistics, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, market, save, RESULTS

m = market()
A = {r['item']: num(r['value']) for r in read('model_assumptions.csv')}
act = {r['quarter']: r for r in read('actuals_quarterly.csv')}
cons = {r['period']: r for r in read('consensus_2026-10-28.csv')}
fc = {r['scenario']: r for r in read('stablecoin_forecasts.csv')}
HLQ = {r['item']: num(r['value']) for r in read('hyperliquid_q3.csv', folder='results')}
curve = read('treasury_par_yield_curve_2026.csv')
cv = max(curve, key=lambda r: (r['Date'][6:], r['Date'][:5]))
par = {k: num(cv[k]) for k in ('3 Mo', '6 Mo', '1 Yr', '2 Yr')}
GAP = A['bill_gap_pt']
MARG = 1 - m['rate_sens_distribution_cost_per_100bp_musd'] / m['rate_sens_reserve_income_per_100bp_musd']
DRAG = {r['item']: num(r['value']) for r in read('rate_drag.csv', folder='results')}['drag_per_100bp_pct'] / 100
supply = read('stablecoin_supply_daily.csv')

# forward 3-month path by quarter from the par curve (par ~ zero at the short end)
f_6m = 2 * par['6 Mo'] - par['3 Mo']             # 3m rate starting in 3 months
f_6_12 = 2 * par['1 Yr'] - par['6 Mo']            # 6m rate starting in 6 months
f_1_2 = 2 * par['2 Yr'] - par['1 Yr']             # 1y rate starting in 1 year
bill = {'Q1-27': (f_6m + f_6_12) / 2, 'Q2-27': f_6_12, 'Q3-27': (f_6_12 + f_1_2) / 2, 'Q4-27': f_1_2}
Q = ['Q3-26', 'Q4-26', 'Q1-27', 'Q2-27', 'Q3-27', 'Q4-27']
DAYS = {'Q3-26': 92, 'Q4-26': 92, 'Q1-27': 90, 'Q2-27': 91, 'Q3-27': 92, 'Q4-27': 92}
rr = {'Q3-26': A['reserve_return_q3_26_pct'], 'Q4-26': A['reserve_return_q4_26_pct']}
rr.update({k: v - GAP for k, v in bill.items()})

# float: Q3 measured average; Q4 October-to-date average; then the JPMorgan path, less the rate drag
cal = A['usdc_avg_q3_26_bn'] / statistics.mean(float(r['usdc_usd']) / 1e9 for r in supply if '2026-07-01' <= r['date'] <= '2026-09-30')
oct_avg = statistics.mean(float(r['usdc_usd']) / 1e9 for r in supply if r['date'] >= '2026-10-01') * cal
r_ = fc['jpmorgan']; yrs = int(r_['by_year_end']) - 2026 + 2 / 12
g = (num(r_['target_bn']) / float(supply[-1]['all_stablecoins_usd']) * 1e9) ** (1 / yrs) - 1
flt = {'Q3-26': A['usdc_avg_q3_26_bn'], 'Q4-26': oct_avg}
base = oct_avg
for i, qq in enumerate(Q[2:], 1):
    base *= (1 + g) ** 0.25
    flt[qq] = base * (1 - DRAG * (rr[qq] - A['reserve_return_today_pct']))
end_usdc = {'Q3-26': 73.749}  # placeholder replaced below by the 30 Sep supply
end_usdc['Q3-26'] = float([r for r in supply if r['date'] == '2026-09-30'][0]['usdc_usd']) / 1e9 * cal
for i, qq in enumerate(Q[1:], 1):
    end_usdc[qq] = flt[qq] * (1 + g) ** 0.125 if i > 1 else float(supply[-1]['usdc_usd']) / 1e9 * cal

K0, Y0 = HLQ['q3_keep_mid_bias_adjusted'] / 100, A['keep_base_yield_pct']
MU = MARG if A['use_rate_table_for_keep'] else K0     # keep held as yields move unless the rate table is switched on
def kept(f, y, d): return f * (Y0 * K0 + (y - Y0) * MU) / 100 * 1000 * d / 365

# opening balance sheet, 30 Jun 2026 ($m)
a2 = act['Q2-26']
cash = num(a2['corporate_cash_end'])
seg_corp = 889.311
ppe_intang = 22.177 + 446.577 + 265.742          # fixed assets, intangibles, goodwill
other_assets = num(a2['total_assets_end']) - cash - 73161.172 - seg_corp - ppe_intang
deposits = 72927.544
excess = 73161.172 - deposits                     # reserves held above the USDC liability at 30 Jun, carried flat
deferred = 242.2 - 0.0                            # ARC presale, gross, in other current liabilities
recv_arc = A['arc_receivable_musd']
other_liab = num(a2['total_liabilities_end']) - deposits - deferred
equity = num(a2['total_assets_end']) - num(a2['total_liabilities_end'])   # includes a $1.4m noncontrolling interest
other_assets -= 0  # includes the $20.2m ARC receivable
shares_prev = num(a2['diluted_shares_m'])
taz_sh = A['tazapay_consideration_musd'] / m['crcl_price']
OPEN = dict(usdc_growth_jpmorgan=g, usdc_avg_q4_26_bn=oct_avg, usdc_end_q3_26_bn=end_usdc['Q3-26'], usdc_end_q4_26_bn=end_usdc['Q4-26'],
            par_3m=par['3 Mo'], par_6m=par['6 Mo'], par_1y=par['1 Yr'], par_2y=par['2 Yr'], curve_date=cv['Date'], marginal_keep=MARG, use_rate_table=A['use_rate_table_for_keep'],
            cash=cash, segregated_corporate=seg_corp, reserve_excess=excess, ppe_intangibles_goodwill=ppe_intang, other_assets=other_assets,
            deferred_arc=deferred, other_liabilities=other_liab, equity=equity, diluted_shares_q2=shares_prev, tazapay_shares_m=taz_sh)
CASH0, PPE0, OA0, DEF0, EQ0, SH0 = cash, ppe_intang, other_assets, deferred, equity, shares_prev

def build(tax27):
    """Runs the quarters. tax27 is the 2027 effective tax rate (%), set by the NOL schedule below."""
    cash, ppe_intang, other_assets, deferred, equity, shares_prev = CASH0, PPE0, OA0, DEF0, EQ0, SH0
    F = {}
    for i, qq in enumerate(Q):
        d = DAYS[qq]; yr = 2026 if qq.endswith('26') else 2027
        ri = flt[qq] * rr[qq] / 100 * 1000 * d / 365
        kp = kept(flt[qq], rr[qq], d)
        dtc = ri - kp
        oth = A['other_revenue_ex_arc_h2_26_musd'] / 2 if yr == 2026 else A['other_revenue_ex_arc_h2_26_musd'] / 2 * (1 + A['other_revenue_ex_arc_growth_2027_pct'] / 100)
        arc = {'Q3-26': A['arc_revenue_q3_26_musd'], 'Q4-26': A['arc_revenue_q4_26_musd'], 'Q1-27': A['arc_revenue_2027_musd'] / 2, 'Q2-27': A['arc_revenue_2027_musd'] / 2}.get(qq, 0.0)
        rev = ri + oth + arc
        oc = A['other_costs_qtr_musd']
        rldc = rev - dtc - oc
        adj = (A['adj_opex_fy26_musd'] - A['adj_opex_h1_26_musd']) / 2 if yr == 2026 else A['adj_opex_fy26_musd'] / 4 * (1 + A['adj_opex_growth_2027_pct'] / 100)
        sbc = A['sbc_qtr_musd'] * 1.0125 ** (i + 1); da = A['da_qtr_musd']; oth_op = A['gaap_opex_other_items_qtr_musd']
        opex = adj + sbc + da + oth_op
        op = rldc - opex
        interest = cash * (rr[qq] + GAP) / 100 * d / 365
        pre = op + interest
        taxr = A['tax_rate_2026_pct'] if yr == 2026 else tax27
        tax = pre * taxr / 100; ni = pre - tax
        sh = shares_prev * (1 + A['share_drift_qtr_pct'] / 100)
        if qq == 'Q3-26': sh = shares_prev + A['binance_shares_m'] * 14 / 92
        if qq == 'Q4-26': sh = shares_prev * (1 + A['share_drift_qtr_pct'] / 100) + A['binance_shares_m'] * 78 / 92
        if qq == 'Q2-27': sh += taz_sh * 0.5
        if qq == 'Q3-27': sh += taz_sh * 0.5
        shares_prev = sh
        eps = ni / sh
        eps_ex = (ni - arc * (1 - taxr / 100)) / sh
        eps_lowtax = pre * (1 - A['tax_rate_2026_pct'] / 100) / sh
        owner = (rldc - arc - adj - sbc - da) * 0.79 / sh
        # cash flow
        recv = recv_arc if qq == 'Q3-26' else 0.0
        cfo = ni + sbc + da - arc + recv
        capex = A['capex_qtr_musd']
        taz = A['tazapay_consideration_musd'] if qq == 'Q2-27' else 0.0
        cff = (A['binance_placement_cash_musd'] if qq == 'Q3-26' else 0.0) + A['option_proceeds_qtr_musd'] - A['rsu_withholding_qtr_musd']
        cash += cfo - capex + cff
        # balance sheet
        ppe_intang += capex - da + taz           # Tazapay at its $400m price, paid in shares (goodwill/intangibles)
        other_assets -= recv
        deferred -= arc
        deposits_q = end_usdc[qq] * 1000
        assets = cash + seg_corp + deposits_q + excess + ppe_intang + other_assets
        liab = deposits_q + deferred + other_liab
        equity += ni + sbc + (A['binance_placement_cash_musd'] if qq == 'Q3-26' else 0.0) + A['option_proceeds_qtr_musd'] - A['rsu_withholding_qtr_musd'] + taz
        F[qq] = dict(usdc_avg_bn=flt[qq], reserve_return_pct=rr[qq], reserve_income=ri, distribution_transaction_costs=dtc, keep_pct=kp / ri * 100,
                     other_revenue_ex_arc=oth, arc_revenue=arc, total_revenue=rev, other_costs=oc, rldc=rldc, rldc_margin_pct=rldc / rev * 100,
                     adj_opex=adj, adj_ebitda=rldc - adj, stock_pay=sbc, da=da, other_gaap_opex=oth_op, operating_income=op, interest_income=interest,
                     pretax=pre, tax=tax, net_income=ni, diluted_shares_m=sh, eps_gaap=eps, eps_ex_arc=eps_ex, eps_gaap_at_5pct_tax=eps_lowtax, owner_eps=owner,
                     cfo=cfo, capex=capex, fcf=cfo - capex, financing_ex_deposits=cff,
                     corporate_cash=cash, segregated_corporate_stablecoins=seg_corp, reserves_for_holders=deposits_q + excess, ppe_intangibles_goodwill=ppe_intang,
                     other_assets=other_assets, total_assets=assets, deposits_from_holders=deposits_q, deferred_revenue_arc=deferred, other_liabilities=other_liab,
                     total_liabilities=liab, equity=assets - liab, equity_roll=equity, balance_check=assets - liab - equity)
    return F

# Tax. Circle keeps a full valuation allowance on its US deferred tax assets and had $478.8m of federal NOLs at the end of
# 2025, usable against 80% of taxable income a year (10-K FY25, note 13). In H1-26 the NOLs and stock-pay deductions
# sheltered US income and the 5.1% rate was mostly non-US tax (10-Q Q2-26). So 2026 stays at 5.1%. For 2027: the NOLs left
# after 2026 shelter 80% of taxable income until they run out; federal tax at 21% on the rest, on top of the 5.1%.
# I treat book pretax income as taxable income, which ignores further stock-pay deductions (so it leans high). A release of
# the valuation allowance would be a one-off GAAP tax benefit; it is left out.
NOL0 = A['federal_nol_end_2025_musd']
def tax_2027(F):
    pre26 = A['pretax_h1_26_musd'] + F['Q3-26']['pretax'] + F['Q4-26']['pretax']
    left = max(0.0, NOL0 - 0.8 * pre26)
    pre27 = sum(F[q]['pretax'] for q in ('Q1-27', 'Q2-27', 'Q3-27', 'Q4-27'))
    used = min(left, 0.8 * pre27)
    fed = 0.21 * max(0.0, pre27 - used)
    return A['tax_rate_2026_pct'] + fed / pre27 * 100, left, used, pre26, pre27
F = build(A['tax_rate_2026_pct'])
for _ in range(3):
    T27, NOL_LEFT, NOL_USED, PRE26, PRE27 = tax_2027(F)
    F = build(T27)

# FY totals with actual H1
h1 = {k: num(act['Q1-26'][c]) + num(act['Q2-26'][c]) for k, c in (('total_revenue', 'total_revenue'), ('reserve_income', 'reserve_income'),
      ('net_income', 'net_income'), ('distribution_transaction_costs', 'distribution_transaction_costs'))}
h1['eps_gaap'] = num(act['Q1-26']['diluted_eps']) + num(act['Q2-26']['diluted_eps'])
def fy(year):
    qs = [qq for qq in Q if qq.endswith(str(year)[2:])]
    out = {k: sum(F[qq][k] for qq in qs) for k in ('total_revenue', 'reserve_income', 'distribution_transaction_costs', 'net_income', 'eps_gaap', 'eps_ex_arc', 'eps_gaap_at_5pct_tax', 'owner_eps', 'adj_ebitda', 'arc_revenue')}
    if year == 2026:
        for k in ('total_revenue', 'reserve_income', 'distribution_transaction_costs', 'net_income', 'eps_gaap'):
            out[k] += h1[k]
        out['eps_ex_arc'] += h1['eps_gaap']; out['eps_gaap_at_5pct_tax'] += h1['eps_gaap']
    out['keep_pct'] = (out['reserve_income'] - out['distribution_transaction_costs']) / out['reserve_income'] * 100
    return out
FY = {'FY26': fy(2026), 'FY27': fy(2027)}

L = [f"Base case: USDC Q3-26 ${flt['Q3-26']:.1f}bn, Q4-26 ${flt['Q4-26']:.1f}bn (October to date), then JPMorgan's path ({g:.1%} a year) less a {DRAG:.0%}-per-100bp rate drag",
     f"Reserve return: Q3-26 {rr['Q3-26']:.2f}%, Q4-26 {rr['Q4-26']:.2f}%, then the Treasury forward curve ({cv['Date']}) less {GAP}pt: "
     + ', '.join(f"{k} {rr[k]:.2f}%" for k in Q[2:]),
     f"Keep: {K0:.1%} (measured Q3, corrected for the backtest's average miss), " + (f"plus {MARG:.1%} of any change in yield" if A['use_rate_table_for_keep'] else 'held as yields move'), '']
for qq in Q:
    f = F[qq]
    L.append(f"{qq}: USDC ${f['usdc_avg_bn']:.1f}bn | RI ${f['reserve_income']:.0f}m | keep {f['keep_pct']:.1f}% | revenue ${f['total_revenue']:.0f}m | RLDC {f['rldc_margin_pct']:.1f}% | "
             f"adj EBITDA ${f['adj_ebitda']:.0f}m | NI ${f['net_income']:.0f}m | GAAP EPS ${f['eps_gaap']:.2f} (ex-ARC ${f['eps_ex_arc']:.2f}) | cash ${f['corporate_cash']:.0f}m | check {f['balance_check']:+.2f}")
L.append('')
L.append('Against consensus (GAAP diluted EPS; total revenue and reserve income):')
rows = []
for p, f in (('Q3-26', F['Q3-26']), ('Q4-26', F['Q4-26']), ('FY26', FY['FY26']), ('FY27', FY['FY27'])):
    c = cons[p]
    rows.append([p, f"{f['total_revenue']:.0f}", c['revenue_musd_yahoo'], f"{f['total_revenue'] / num(c['revenue_musd_yahoo']) - 1:+.1%}",
                 f"{f['eps_gaap']:.2f}", c['eps_yahoo'], c['eps_nasdaq'], f"{f['eps_gaap'] / num(c['eps_yahoo']) - 1:+.0%}",
                 f"{f['eps_gaap_at_5pct_tax']:.2f}", f"{f['eps_ex_arc']:.2f}", f"{f['keep_pct']:.1f}"])
    L.append(f"  {p}: revenue ${f['total_revenue']:.0f}m vs ${num(c['revenue_musd_yahoo']):.0f}m ({f['total_revenue'] / num(c['revenue_musd_yahoo']) - 1:+.1%}); "
             f"GAAP EPS ${f['eps_gaap']:.2f} vs ${num(c['eps_yahoo']):.3f} Yahoo / ${num(c['eps_nasdaq']):.2f} Nasdaq; at a 5.1% tax rate ${f['eps_gaap_at_5pct_tax']:.2f}; ex-ARC ${f['eps_ex_arc']:.2f}; keep {f['keep_pct']:.1f}%")
# ---- Line by line against the Street and Circle's guidance ----
# Free sources carry only revenue and EPS consensus. So: my lines, the Street's revenue and EPS, Circle's FY26 guidance
# (Q2-26 call: other revenue $310m-$330m incl. ~$180m ARC; RLDC margin 41.7%-43.7% incl. ARC; adjusted opex $570m-$585m,
# "higher end"), and what the Street's EPS implies for costs given its revenue.
h1l = {}
for c in ('total_revenue', 'reserve_income', 'other_revenue', 'distribution_transaction_costs', 'other_costs', 'net_income'):
    h1l[c] = num(act['Q1-26'][c]) + num(act['Q2-26'][c])
h1l['rldc'] = h1l['total_revenue'] - h1l['distribution_transaction_costs'] - h1l['other_costs']
h1l['adj_opex'] = A['adj_opex_h1_26_musd']; h1l['adj_ebitda'] = h1l['rldc'] - h1l['adj_opex']
def line(qs, with_h1=False):
    o = {k: sum(F[q][k] for q in qs) for k in ('reserve_income', 'other_revenue_ex_arc', 'arc_revenue', 'total_revenue', 'distribution_transaction_costs',
                                              'rldc', 'adj_opex', 'adj_ebitda', 'stock_pay', 'da', 'other_gaap_opex', 'interest_income', 'pretax', 'tax', 'net_income', 'eps_gaap', 'eps_ex_arc')}
    if with_h1:
        o['reserve_income'] += h1l['reserve_income']; o['other_revenue_ex_arc'] += h1l['other_revenue']; o['total_revenue'] += h1l['total_revenue']
        o['distribution_transaction_costs'] += h1l['distribution_transaction_costs']; o['rldc'] += h1l['rldc']; o['adj_opex'] += h1l['adj_opex']
        o['adj_ebitda'] += h1l['adj_ebitda']; o['net_income'] += h1l['net_income']; o['eps_gaap'] += h1['eps_gaap']; o['eps_ex_arc'] += h1['eps_gaap']
    o['rldc_margin'] = o['rldc'] / o['total_revenue']; o['keep'] = 1 - o['distribution_transaction_costs'] / o['reserve_income']
    return o
LI = {'Q3-26': line(['Q3-26']), 'Q4-26': line(['Q4-26']), 'FY26': line(['Q3-26', 'Q4-26'], True), 'FY27': line(['Q1-27', 'Q2-27', 'Q3-27', 'Q4-27'])}
GUIDE = dict(other_lo=310, other_hi=330, rldc_m_lo=0.417, rldc_m_hi=0.437, opex_lo=570, opex_hi=585)
L.append('')
L.append('Line by line (my numbers; Street revenue/EPS from Yahoo; Circle FY26 guidance from the Q2-26 call):')
for p_, o in LI.items():
    L.append(f"  {p_}: RI ${o['reserve_income']:.0f}m | other ex-ARC ${o['other_revenue_ex_arc']:.0f}m | ARC ${o['arc_revenue']:.0f}m | revenue ${o['total_revenue']:.0f}m | "
             f"distribution ${o['distribution_transaction_costs']:.0f}m (keep {o['keep']:.1%}) | RLDC ${o['rldc']:.0f}m ({o['rldc_margin']:.1%}) | adj opex ${o['adj_opex']:.0f}m | "
             f"adj EBITDA ${o['adj_ebitda']:.0f}m | NI ${o['net_income']:.0f}m | EPS ${o['eps_gaap']:.2f}")
fy = LI['FY26']; sr = num(cons['FY26']['revenue_musd_yahoo'])
L.append(f"  FY26 vs guidance: other revenue ${fy['other_revenue_ex_arc'] + fy['arc_revenue']:.0f}m (guide ${GUIDE['other_lo']}m-${GUIDE['other_hi']}m); "
         f"RLDC margin {fy['rldc_margin']:.1%} (guide {GUIDE['rldc_m_lo']:.1%}-{GUIDE['rldc_m_hi']:.1%}); adj opex ${fy['adj_opex']:.0f}m (guide ${GUIDE['opex_lo']}m-${GUIDE['opex_hi']}m)")
L.append(f"  Guidance-implied FY26 adj EBITDA on the Street's ${sr:.0f}m revenue: ${sr * GUIDE['rldc_m_lo'] - GUIDE['opex_hi']:.0f}m to ${sr * GUIDE['rldc_m_hi'] - GUIDE['opex_lo']:.0f}m; mine ${fy['adj_ebitda']:.0f}m")
# Q4: where the Street's $0.33 can come from
q4 = F['Q4-26']; t = A['tax_rate_2026_pct'] / 100; sh4 = q4['diluted_shares_m']; cash_open4 = F['Q3-26']['corporate_cash']
def q4_eps_at(rr_new):
    dri = q4['usdc_avg_bn'] * (rr_new - q4['reserve_return_pct']) / 100 * 1000 * DAYS['Q4-26'] / 365
    dint = cash_open4 * (rr_new - q4['reserve_return_pct']) / 100 * DAYS['Q4-26'] / 365
    return q4['eps_gaap'] + (dri * K0 + dint) * (1 - t) / sh4
st_rev4, st_eps4 = num(cons['Q4-26']['revenue_musd_yahoo']), num(cons['Q4-26']['eps_yahoo'])
arc_impl4 = st_rev4 - q4['reserve_income'] - q4['other_revenue_ex_arc']
eps_arc_impl = q4['eps_gaap'] + (arc_impl4 - q4['arc_revenue']) * (1 - t) / sh4
cost_gap = (eps_arc_impl - st_eps4) * sh4 / (1 - t)
keep_needed = (q4['reserve_income'] - q4['distribution_transaction_costs'] - cost_gap) / q4['reserve_income']
L.append(f"Q4-26 walk: my GAAP EPS ${q4['eps_gaap']:.2f} at a {q4['reserve_return_pct']:.2f}% reserve return; ${q4_eps_at(3.76):.2f} at 3.76% (fund at end-Sep less 0.08pt); ${q4_eps_at(3.55):.2f} at Q3's 3.55%.")
L.append(f"  The Street's Q4 revenue (${st_rev4:.0f}m) on my reserve income implies ${arc_impl4:.0f}m of ARC; with that, my EPS is ${eps_arc_impl:.2f}. "
         f"Getting to the Street's ${st_eps4:.3f} then needs ${cost_gap:.0f}m less pretax income in Q4: a keep of {keep_needed:.1%} instead of {q4['keep_pct']:.1f}%, "
         f"adjusted opex of ${q4['adj_opex'] + cost_gap:.0f}m instead of the ${q4['adj_opex']:.0f}m Circle's FY guide leaves for each H2 quarter, "
         f"or less of the ${q4['interest_income']:.0f}m I have Circle earning on its own cash.")
e355 = q4_eps_at(3.55)
L.append(f"  Two assumptions close it: Q3's {3.55:.2f}% reserve return gives ${e355:.2f}, and a 21% tax rate on that instead of {A['tax_rate_2026_pct']}% gives ${e355 * 0.79 / (1 - t):.2f}.")
L.append(f"2027 tax: federal NOLs left after 2026 ${NOL_LEFT:.0f}m (from $478.8m, 80% limit, 2026 pretax ${PRE26:.0f}m), all used in 2027 against ${PRE27:.0f}m pretax; "
         f"2027 effective rate {T27:.1f}% (5.1% non-federal + federal on the unsheltered part). Valuation-allowance release left out.")
with open(os.path.join(RESULTS, 'table_line_items.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['$m unless stated', 'Q3-26 mine', 'Q4-26 mine', 'FY26 mine', 'FY26 Circle guidance', 'FY27 mine', 'Q3-26 Street', 'Q4-26 Street', 'FY26 Street', 'FY27 Street'])
    cs_ = lambda p_, k: cons[p_][k]
    rows_ = [('Reserve income', 'reserve_income', ''), ('Other revenue ex-ARC', 'other_revenue_ex_arc', ''), ('ARC token revenue', 'arc_revenue', ''),
             ('Total revenue', 'total_revenue', ''), ('Distribution and transaction costs', 'distribution_transaction_costs', ''), ('Keep (% of reserve income)', 'keep', ''),
             ('RLDC', 'rldc', ''), ('RLDC margin', 'rldc_margin', f"{GUIDE['rldc_m_lo']:.1%}-{GUIDE['rldc_m_hi']:.1%}"),
             ('Adjusted opex', 'adj_opex', f"{GUIDE['opex_lo']}-{GUIDE['opex_hi']}"), ('Adjusted EBITDA', 'adj_ebitda', f"{sr * GUIDE['rldc_m_lo'] - GUIDE['opex_hi']:.0f}-{sr * GUIDE['rldc_m_hi'] - GUIDE['opex_lo']:.0f} (on Street revenue)"),
             ('Net income', 'net_income', ''), ('GAAP diluted EPS ($)', 'eps_gaap', ''), ('EPS ex-ARC ($)', 'eps_ex_arc', '')]
    for lab, k, gd in rows_:
        fmt = (lambda v: f"{v:.1%}") if k in ('keep', 'rldc_margin') else (lambda v: f"{v:.2f}") if k.startswith('eps') else (lambda v: f"{v:.0f}")
        street = ['', '', '', '']
        if k == 'total_revenue': street = [cs_(p_, 'revenue_musd_yahoo') for p_ in ('Q3-26', 'Q4-26', 'FY26', 'FY27')]
        if k == 'eps_gaap': street = [f"{cs_(p_, 'eps_yahoo')} / {cs_(p_, 'eps_nasdaq')}" for p_ in ('Q3-26', 'Q4-26', 'FY26', 'FY27')]
        if k == 'other_revenue_ex_arc': gd = f"{GUIDE['other_lo']}-{GUIDE['other_hi']} incl. ~180 ARC"
        w.writerow([lab, fmt(LI['Q3-26'][k]), fmt(LI['Q4-26'][k]), fmt(LI['FY26'][k]), gd, fmt(LI['FY27'][k])] + street)
# ---- The headline call: Q3-26 EPS ex-ARC, with a range ----
# Scored as (GAAP net income attributable to common stockholders - ARC token revenue x (1 - the quarter's effective tax rate))
# / diluted shares, all from Circle's Q3-26 filing. Range: keep 34.7% to 36.7% (the #248 band) and adjusted opex
# $10m either side of my $152m.
_f = F['Q3-26']; _t = A['tax_rate_2026_pct'] / 100; _sh = _f['diluted_shares_m']
per_keep_pt = _f['reserve_income'] * 0.01 * (1 - _t) / _sh
per_10m = 10 * (1 - _t) / _sh
KEEP_ADJ = (_f['keep_pct'] / 100 - 0.347) , (0.367 - _f['keep_pct'] / 100)
EXARC_LO = _f['eps_ex_arc'] - KEEP_ADJ[0] * 100 * per_keep_pt - per_10m
EXARC_HI = _f['eps_ex_arc'] + KEEP_ADJ[1] * 100 * per_keep_pt + per_10m
L.append('')
L.append(f"Headline call, Q3-26 EPS ex-ARC: ${_f['eps_ex_arc']:.2f}; each point of keep moves it ${per_keep_pt:.3f}, each $10m of opex ${per_10m:.3f}; "
         f"range ${EXARC_LO:.2f} to ${EXARC_HI:.2f} (keep 34.7% to 36.7%, opex +/- $10m)")
with open(os.path.join(RESULTS, 'headline_call.csv'), 'w') as fh:
    fh.write(f"item,value\neps_ex_arc_q3_26,{_f['eps_ex_arc']:.4f}\nrange_low,{EXARC_LO:.4f}\nrange_high,{EXARC_HI:.4f}\nper_keep_point,{per_keep_pt:.4f}\nper_10m_opex,{per_10m:.4f}\n")
f3 = F['Q3-26']; t3 = A['tax_rate_2026_pct'] / 100
L.append('')
L.append('ARC timing (Q3-26 GAAP EPS if ARC revenue in the quarter is $0, $90m or $180m; each $10m is about '
         f"${10 * (1 - t3) / f3['diluted_shares_m']:.3f}):")
for arc in (0, 90, 180):
    L.append(f"  ARC ${arc}m: Q3 revenue ${f3['total_revenue'] - f3['arc_revenue'] + arc:.0f}m, GAAP EPS ${f3['eps_ex_arc'] + arc * (1 - t3) / f3['diluted_shares_m']:.2f}")
L.append(f"The Street's Q3 revenue (${num(cons['Q3-26']['revenue_musd_yahoo']):.0f}m) only fits if it includes roughly ${num(cons['Q3-26']['revenue_musd_yahoo']) - (f3['total_revenue'] - f3['arc_revenue']):.0f}m of ARC revenue on my reserve income.")
save('model.txt', '\n'.join(L) + '\n')
with open(os.path.join(RESULTS, 'table_vs_consensus.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Period', 'My revenue ($m)', 'Consensus revenue ($m, Yahoo)', 'Revenue gap', 'My GAAP EPS', 'Consensus EPS (Yahoo)', 'Consensus EPS (Nasdaq/Zacks)', 'EPS gap vs Yahoo', 'My GAAP EPS at 5.1% tax', 'My EPS ex-ARC', 'My keep (%)'])
    w.writerows(rows)
with open(os.path.join(RESULTS, 'model_quarterly.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); keys = list(F['Q3-26'].keys())
    w.writerow(['line ($m unless stated)'] + Q)
    for k in keys: w.writerow([k] + [round(F[qq][k], 4) for qq in Q])
with open(os.path.join(RESULTS, 'model_inputs.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['item', 'value'])
    for k, v in OPEN.items(): w.writerow([k, v])
