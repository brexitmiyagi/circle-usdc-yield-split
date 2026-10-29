# The keep method, in one place, so the backtest and the Q3-26 estimate use exactly the same arithmetic.
# Split Circle's reserve income into three parts: Hyperliquid's USDC, Binance customers' USDC, and everything else.
#   - Hyperliquid: measured. USDC in Circle's Core Deposit Wallet earns Circle the full yield (Circle's platform), USDC in
#     Coinbase's treasury earns Circle nothing (Coinbase's platform), USDC in the legacy Arbitrum bridge is shared-pool USDC
#     and earns Circle its shared-pool take s.
#   - Binance customers' USDC (Binance's own monthly reserve reports): Circle keeps about a third of the yield on it
#     (1.0 to 1.34 cents of 4.06, distribution_history.py). The low end of each range counts it; the high end leaves it in
#     "everything else".
#   - Everything else keeps last quarter's keep. (Moving it for yield at Circle's own 51.2% marginal rate is an option;
#     the backtest shows it made the past four quarters worse, so the Q3 estimate leaves it off.)
# s, Circle's take on a shared-pool dollar, comes from the quarter before (no look-ahead): low = half of (yield less the
# deductions taken before the 50/50 split), high = yield less Coinbase's take of the shared pool.
import os, sys, datetime as dt, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read, num, market

m = market()
MARG = 1 - m['rate_sens_distribution_cost_per_100bp_musd'] / m['rate_sens_reserve_income_per_100bp_musd']
BIN_SHARE = 1.34 / 4.06          # Circle's share of the yield on Binance customers' USDC (low-end case)

Q = {'Q2-25': (dt.date(2025, 4, 1), dt.date(2025, 6, 30)), 'Q3-25': (dt.date(2025, 7, 1), dt.date(2025, 9, 30)),
     'Q4-25': (dt.date(2025, 10, 1), dt.date(2025, 12, 31)), 'Q1-26': (dt.date(2026, 1, 1), dt.date(2026, 3, 31)),
     'Q2-26': (dt.date(2026, 4, 1), dt.date(2026, 6, 30)), 'Q3-26': (dt.date(2026, 7, 1), dt.date(2026, 9, 30))}
ORDER = list(Q)

cq = {r['quarter']: r for r in read('circle_quarterly.csv')}
ys = {r['quarter']: r for r in read('yield_split.csv', folder='results')}
# Q4-25 average USDC isn't printed; derive it from the FY25 average as yield_split.py does
_d = {'Q1-25': 90, 'Q2-25': 91, 'Q3-25': 92}
Q4_AVG = (64.870 * 365 - sum(num(cq[q]['usdc_avg_bn']) * _d[q] for q in _d)) / 92

oc = {dt.date.fromisoformat(r['date']): r for r in read('hyperliquid_split_onchain_daily.csv')}
tre = {k: num(v['treasury_usdc']) / 1e9 for k, v in oc.items()}
cdw = {k: num(v['circle_linked_usdc']) / 1e9 for k, v in oc.items()}
arb = {dt.date.fromisoformat(r['date']): num(r['arbitrum_bridge_usd']) / 1e9 for r in read('hyperliquid_bridge_defillama.csv')}
por = {dt.date.fromisoformat(r['snapshot']): num(r['customer_liability_musd']) / 1000 for r in read('binance_por_usdc.csv')}


def avg(series, q, default=0.0):
    a, b = Q[q]; d = a; vals = []
    while d <= b:
        vals.append(series.get(d, default)); d += dt.timedelta(days=1)
    return statistics.mean(vals)


def bin_avg(q):
    a, b = Q[q]; b = b + dt.timedelta(days=1)
    pts = [por[k] for k in sorted(por) if a <= k <= b]
    return (pts[0] / 2 + sum(pts[1:-1]) + pts[-1] / 2) / (len(pts) - 1)


def days(q):
    a, b = Q[q]; return (b - a).days + 1


def actual(q):
    r = cq[q]; ri = num(r['reserve_income_musd']); kept = ri - num(r['distribution_transaction_costs_musd'])
    usdc = num(r['usdc_avg_bn']) if r['usdc_avg_bn'] else Q4_AVG
    return dict(ri=ri, kept=kept, keep=kept / ri, y=ri / (usdc * 1000 * days(q) / 365), days=days(q))


def parts(q, y, s, with_binance):
    f = days(q) / 365 * 1000
    c, t, a = avg(cdw, q), avg(tre, q), avg(arb, q)
    ri_hl, kept_hl = (c + t + a) * y * f, (c * y + a * s) * f
    if with_binance:
        b = bin_avg(q); ri_bn, kept_bn = b * y * f, b * y * BIN_SHARE * f
    else:
        ri_bn = kept_bn = 0.0
    return ri_hl + ri_bn, kept_hl + kept_bn


def s_range(q_prev, y):
    r = ys[q_prev]
    ded = num(r['deductions_before_split_bp_of_float']) / 1e4
    cb = num(r['coinbase_take_of_shared_pct']) / 100
    return 0.5 * (y - ded), y * (1 - cb)


def predict(q_prev, q, ri, y, with_binance, s, yield_adjust=False):
    """Keep in quarter q from quarter q_prev's actuals, the measured flows and the yield (ri and y for quarter q)."""
    p = actual(q_prev)
    s_prev = s_range(ORDER[ORDER.index(q_prev) - 1], p['y'])[0 if s == 'low' else 1] if ORDER.index(q_prev) > 0 else None
    s_now = s_range(q_prev, y)[0 if s == 'low' else 1]
    if s_prev is None:
        s_prev = s_now
    ri_x0, kept_x0 = parts(q_prev, p['y'], s_prev, with_binance)
    k_other = (p['kept'] - kept_x0) / (p['ri'] - ri_x0)
    if yield_adjust:
        k_other = (p['y'] * k_other + (y - p['y']) * MARG) / y
    ri_x1, kept_x1 = parts(q, y, s_now, with_binance)
    return (k_other * (ri - ri_x1) + kept_x1) / ri


def keep_range(q_prev, q, ri, y, yield_adjust=False):
    """Low end: Binance counted. High end: Binance left in everything else. Each over both values of s."""
    lo = min(predict(q_prev, q, ri, y, True, s, yield_adjust) for s in ('low', 'high'))
    hi = max(predict(q_prev, q, ri, y, False, s, yield_adjust) for s in ('low', 'high'))
    return lo, hi
