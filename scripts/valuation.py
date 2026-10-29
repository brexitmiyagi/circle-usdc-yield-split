# The price target. Owner earnings (stock pay a cost, ARC presale left out, statutory tax) on USDC paths anchored to three
# published stablecoin forecasts, with:
#   - reserve returns from the Treasury forward curve (26 Oct) less Circle's usual gap to the 3-month bill
#   - Circle keeping the measured Q3 share (keep_method.py, backtest-corrected), held as yields move; rate table as a sensitivity
#   - higher rates taking some USDC away, and lower rates adding it: the drag estimated in rate_drag.py from monthly data
#   - costs moving with the float: operating costs and stock pay grow at half the float's growth, between 0% and 5% a year
#   - balance sheet added once: corporate cash, the ARC receivable, Binance's $100m, Circle's 25% of Arc at the presale
#     price, Tazapay at its $400m price with the shares it costs, and the federal NOLs left at 30 Jun 2026 (21% tax shield)
# Discounted at the CAPM cost of equity (beta.py), 3% after year ten. The 12-month target rolls the value forward one year
# at the cost of equity (no dividends).
# The target uses my own scenario weights, 35% flat, 55% JPMorgan, 10% Standard Chartered. I set them on 27 Oct, before this
# version of the model existed, and haven't moved them since: flat gets more than a third because total stablecoins have
# gone sideways for a year; Standard Chartered gets 10% because the bank pushed its date from 2028 to 2030 on 14 Oct.
# Cross-check: the odds the CRCL options market puts on each scenario (options_implied.py). Roll each scenario's value
# forward to the Jan-2028 expiry at the cost of equity, split the price line halfway between them (geometric midpoints),
# and read the odds of CRCL finishing in each band. Options odds are risk-neutral and lean to the downside.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, market, save, RESULTS
import earnings_power as ep
import options_implied as oi
import math

m = market()
A = {r['item']: num(r['value']) for r in read('model_assumptions.csv')}
supply = read('stablecoin_supply_daily.csv')
M0 = float(supply[-1]['all_stablecoins_usd']) / 1e9
F0 = float(supply[-1]['usdc_usd']) / 1e9
fc = {r['scenario']: r for r in read('stablecoin_forecasts.csv')}
curve = read('treasury_par_yield_curve_2026.csv')
c26 = max(curve, key=lambda r: (r['Date'][6:], r['Date'][:5]))  # latest date in the file
p1, p2, p3 = num(c26['1 Yr']), num(c26['2 Yr']), num(c26['3 Yr'])
f1, f12, f23 = p1, 2 * p2 - p1, 3 * p3 - 2 * p2
GAP = A['bill_gap_pt']
y1 = (2 / 12) * A['reserve_return_q4_26_pct'] + (10 / 12) * ((f1 + f12) / 2 - GAP)   # Nov-26 to Oct-27
FWD = [y1, f12 - GAP] + [f23 - GAP] * 8
FLAT = [A['reserve_return_today_pct']] * 10
HLQ = {r['item']: num(r['value']) for r in read('hyperliquid_q3.csv', folder='results')}
COE = {r['item']: num(r['value']) for r in read('cost_of_equity.csv', folder='results')}
DR = {r['item']: num(r['value']) for r in read('rate_drag.csv', folder='results')}
DRAG = DR['drag_per_100bp_pct'] / 100
K0, Y0 = HLQ['q3_keep_mid_bias_adjusted'] / 100, A['keep_base_yield_pct']   # backtested method, corrected for its average miss
RATE = COE['coe_adjusted_pct'] / 100
MARG = ep.MARG
MU = MARG if A['use_rate_table_for_keep'] else None     # None = keep held at K0 as yields move
CASH = m['corporate_cash_musd'] + A['arc_receivable_musd'] + A['binance_placement_cash_musd']
ARC = A['arc_stake_pct'] / 100 * A['arc_fdv_musd']
TAZ = A['tazapay_consideration_musd']
SHARES = ep.SHARES + A['binance_shares_m'] + TAZ / m['crcl_price']
SCEN = ('flat', 'jpmorgan', 'standard_chartered')
W = {'flat': 0.35, 'jpmorgan': 0.55, 'standard_chartered': 0.10}     # mine, fixed 27 Oct
NOL = 0.21 * (A['federal_nol_end_2025_musd'] - 0.8 * A['pretax_h1_26_musd']) / (1 + COE['coe_adjusted_pct'] / 100) ** 0.75
YLEFT = 2 / 12 + 4 / 365

def path(name):
    r = fc[name]
    if not r['by_year_end']:
        return [0.0] * 4 + [0.03] * 6
    yrs = int(r['by_year_end']) - 2026 + YLEFT
    a = (num(r['target_bn']) / M0) ** (1 / yrs) - 1
    n = int(yrs); frac = yrs - n
    g = [a] * n + [a * frac + 0.10 * (1 - frac)]
    k = 10 - len(g)
    g += [0.10 - 0.07 * i / (k - 1) for i in range(k)] if k > 1 else [0.03] * k
    return g[:10]

def value(name, rates=FWD, drag=DRAG, keep=K0, r=None, marg=MU, share_loss=0.0,
          term=A['terminal_growth_pct'] / 100, arc_haircut=0.0, detail=False):
    r = RATE if r is None else r
    pv = 0; f = F0; opex = ep.OPEX; sbc = ep.SBC; other = ep.OTHER
    rows = []
    for t, g in enumerate(path(name), 1):
        s0 = F0 / M0                                  # USDC's share of all stablecoins today
        f *= (1 + g) * max(0.0, s0 - share_loss * t) / max(1e-9, s0 - share_loss * (t - 1))
        cg = min(0.05, max(0.0, 0.5 * g))
        opex *= 1 + cg; sbc *= 1 + cg; other *= 1 + g
        y = rates[t - 1]
        fe = f * (1 - drag * (y - A['reserve_return_today_pct']))
        kept = fe * (Y0 * keep + (y - Y0) * (keep if marg is None else marg)) / 100 * 1000
        earn = (kept + other - opex - sbc - ep.DA) * (1 - ep.TAX)
        pv += earn / (1 + r) ** t
        rows.append((t, fe, y, kept, earn))
    pv += earn * (1 + term) / (r - term) / (1 + r) ** 10
    eq = pv + CASH + ARC * (1 - arc_haircut) + TAZ + NOL
    return (eq / SHARES, rows) if detail else eq / SHARES

def weighted(**kw):
    return sum(W[k] * value(k, **kw) for k in SCEN)

L = [f'Start: USDC ${F0:.2f}bn, all stablecoins ${M0:.1f}bn. Reserve return path (forward curve less {GAP}pt): '
     f'{", ".join(f"{x:.2f}%" for x in FWD[:3])}, then flat. Keep {K0:.1%}' + (f' at {Y0}% plus {MARG:.1%} of any change.' if MU else ', held as yields move (backtest_keep.py).'),
     f'Added once: cash and receivables ${CASH:.0f}m, Arc stake ${ARC:.0f}m, Tazapay ${TAZ:.0f}m, federal NOL tax shield ${NOL:.0f}m (present value); shares {SHARES:.1f}m '
     f'(Q2 diluted {ep.SHARES:.1f}m + Binance {A["binance_shares_m"]:.2f}m + Tazapay {TAZ / m["crcl_price"]:.2f}m at ${m["crcl_price"]:.2f})']
vals = {}
for k in SCEN:
    v, rows = value(k, detail=True); vals[k] = v
    L.append(f'{k}: value ${v:.2f}; year 1 USDC ${rows[0][1]:.0f}bn earns ${rows[0][4]:.0f}m, year 10 USDC ${rows[-1][1]:.0f}bn earns ${rows[-1][4]:.0f}m')
L.append(f'Discount rate {RATE:.1%} (CAPM, beta.py); float drag {DRAG:.1%} per 1.00pt (rate_drag.py)')

tgt = sum(W[k] * vals[k] for k in SCEN)
PT = tgt * (1 + RATE)
L.append(f'My weights {", ".join(f"{k} {w:.0%}" for k, w in W.items())} (set 27 Oct): ${tgt:.2f} today vs ${m["crcl_price"]:.2f} ({tgt / m["crcl_price"] - 1:+.0%})')
L.append(f'12-month price target: ${tgt:.2f} rolled forward one year at {RATE:.1%} = ${PT:.2f} vs ${m["crcl_price"]:.2f} ({PT / m["crcl_price"] - 1:+.0%})')
base = (W['flat'] * vals['flat'] + W['jpmorgan'] * vals['jpmorgan']) / (W['flat'] + W['jpmorgan'])
IMPLIED_SC = (m["crcl_price"] - base) / (vals["standard_chartered"] - base)
L.append(f'  the price implies a {IMPLIED_SC:.1%} weight on Standard Chartered (rest at my 35:55 flat:JPMorgan ratio)')
# Cross-check: the options market's odds
EXP = '20280121'; T = oi.years(EXP); roll = (1 + RATE) ** T
b1 = math.sqrt(vals['flat'] * vals['jpmorgan']) * roll
b2 = math.sqrt(vals['jpmorgan'] * vals['standard_chartered']) * roll
q1, q2 = oi.prob_above(b1, EXP), oi.prob_above(b2, EXP)
WO = {'flat': 1 - q1, 'jpmorgan': q1 - q2, 'standard_chartered': q2}
vo = sum(WO[k] * vals[k] for k in SCEN)
L.append(f'Cross-check, options market (Jan-2028 expiry, {T:.2f} years, CRCL {oi.S} on 28 Oct): scenario values rolled forward at {RATE:.1%} split at '
         f'${b1:.0f} and ${b2:.0f}; odds below ${b1:.0f} {WO["flat"]:.1%}, ${b1:.0f}-${b2:.0f} {WO["jpmorgan"]:.1%}, above ${b2:.0f} {WO["standard_chartered"]:.1%}; '
         f'value ${vo:.2f}, target ${vo * (1 + RATE):.2f} ({vo * (1 + RATE) / m["crcl_price"] - 1:+.0%})')
L.append(f'  where I differ from the options: {W["flat"] - WO["flat"]:+.1%} on flat, {W["jpmorgan"] - WO["jpmorgan"]:+.1%} on JPMorgan, {W["standard_chartered"] - WO["standard_chartered"]:+.1%} on Standard Chartered')
L.append(f'  rating range (target within 15% of the price = HOLD): price ${PT / 1.15:.2f} to ${PT / 0.85:.2f}')
# The multiple a reader will ask about
MQ = {r[0]: r[1:] for r in __import__('csv').reader(open(os.path.join(RESULTS, 'model_quarterly.csv')))}
eps27 = sum(float(x) for x in MQ['eps_gaap'][2:6]); eps27x = sum(float(x) for x in MQ['eps_ex_arc'][2:6])
L.append(f'Multiples: target ${PT:.2f} is {PT / eps27:.0f}x my 2027 GAAP EPS (${eps27:.2f}) and {PT / eps27x:.0f}x ex-ARC (${eps27x:.2f}); '
         f'the price is {m["crcl_price"] / eps27:.0f}x and {m["crcl_price"] / eps27x:.0f}x')
for k in SCEN:
    _, rows = value(k, detail=True)
    L.append(f'  {k}: owner earnings per share year 3 ${rows[2][4] / SHARES:.2f}, year 5 ${rows[4][4] / SHARES:.2f}, year 10 ${rows[9][4] / SHARES:.2f}')
L.append('Sensitivities of the weighted value:')
for d in (0.0, DR['drag_low_pct'] / 100, DR['drag_high_pct'] / 100, DR['drag_full_sample_pct'] / 100):
    L.append(f'  rate drag {d:.1%} per 1.00pt: ${weighted(drag=d):.2f}')
L.append(f'  yields flat at {A["reserve_return_today_pct"]}% (no drag needed): ${weighted(rates=FLAT, drag=0):.2f}')
for k, lab in ((HLQ['q3_keep_low'] / 100, 'method low, uncorrected'), (HLQ['q3_keep_high'] / 100, 'method high, uncorrected'), (0.385, 'Q2 level, as if no Hyperliquid hit')):
    L.append(f'  keep {k:.1%} ({lab}): ${weighted(keep=k):.2f}')
for r_ in (RATE - 0.01, RATE + 0.01, COE['coe_raw_pct'] / 100):
    L.append(f'  discount rate {r_:.1%}: ${weighted(r=r_):.2f}')
L.append(f'  Arc stake at half the presale price: ${weighted(arc_haircut=0.5):.2f}')
SHARE_SENS = {}
for sl in (0.005, 0.01):
    v_ = weighted(share_loss=sl); SHARE_SENS[sl] = v_
    L.append(f'  USDC losing {sl * 100:.1f} point of stablecoin share a year (from {F0 / M0:.1%}): ${v_:.2f}, target ${v_ * (1 + RATE):.2f}')
for w in ((0.35, 0.55, 0.10), (0.5, 0.45, 0.05), (0.6, 0.4, 0.0)):
    L.append(f'  weights {w[0]:.0%}/{w[1]:.0%}/{w[2]:.0%}: ${w[0] * vals["flat"] + w[1] * vals["jpmorgan"] + w[2] * vals["standard_chartered"]:.2f}')
L.append(f'  keep moving with yield at Circle\'s rate table ({MARG:.1%} of a change): ${weighted(marg=MARG):.2f}' if MU is None else f'  keep held as yields move: ${weighted(marg=None):.2f}')
save('valuation.txt', '\n'.join(L) + '\n')

with open(os.path.join(RESULTS, 'table_valuation.csv'), 'w') as fh:
    labels = {'flat': 'Flat, as the last 12 months', 'jpmorgan': 'JPMorgan, $500-600bn by 2028', 'standard_chartered': 'Standard Chartered, $2tn by 2030'}
    fh.write('Scenario,Stablecoin market,Value per share ($),My weight,Options-market odds\n')
    for k in SCEN:
        fh.write(f'{k},"{labels[k]}",{vals[k]:.2f},{W[k]:.0%},{WO[k]:.1%}\n')
    fh.write(f'Value today,,,{tgt:.2f},{vo:.2f}\n12-month target,,,{PT:.2f},{vo * (1 + RATE):.2f}\n')
with open(os.path.join(RESULTS, 'valuation_summary.csv'), 'w') as fh:
    fh.write('item,value\n')
    for k, v_ in (('value_today', tgt), ('price_target', PT), ('price', m['crcl_price']), ('upside_pct', (PT / m['crcl_price'] - 1) * 100),
                  ('w_flat', W['flat']), ('w_jpmorgan', W['jpmorgan']), ('w_standard_chartered', W['standard_chartered']),
                  ('wo_flat', WO['flat']), ('wo_jpmorgan', WO['jpmorgan']), ('wo_standard_chartered', WO['standard_chartered']),
                  ('band_low', b1), ('band_high', b2), ('options_value', vo), ('options_target', vo * (1 + RATE)), ('keep_used_pct', K0 * 100),
                  ('hold_band_low_price', PT / 1.15), ('hold_band_high_price', PT / 0.85), ('drag_pct', DRAG * 100), ('coe_pct', RATE * 100),
                  ('implied_sc_weight', IMPLIED_SC), ('share_loss_05_value', SHARE_SENS[0.005]), ('share_loss_10_value', SHARE_SENS[0.01]), ('nol_shield_musd', NOL), ('pe_2027_target', PT / eps27), ('pe_2027_exarc_target', PT / eps27x)):
        fh.write(f'{k},{v_:.4f}\n')
