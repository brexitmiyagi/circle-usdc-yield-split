# Does the keep method work? Run it on every quarter I can, using only what was known the quarter before
# (last quarter's actual keep and contract split), plus that quarter's measured flows and yield, and compare with what
# Circle reported. The rule to beat is "same keep as last quarter". I also run the method with the yield adjustment from
# Circle's rate table switched on, and the yield adjustment alone.
# One thing is not available in advance: the backtest divides by the reserve income Circle actually reported, where the
# Q3-26 estimate uses my pre-registered $656m. That only scales the result.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import save, RESULTS
import keep_method as km

L = ['Quarter  actual  method, flows only (range, mid)  same as last  method + yield adj  yield adj only',
     '-------  ------  ---------------------------------  ------------  ------------------  --------------']
rows = []
for q_prev, q in zip(km.ORDER[:-2], km.ORDER[1:-1]):
    a, p = km.actual(q), km.actual(q_prev)
    lo, hi = km.keep_range(q_prev, q, a['ri'], a['y'])
    lo2, hi2 = km.keep_range(q_prev, q, a['ri'], a['y'], yield_adjust=True)
    mid, mid2 = (lo + hi) / 2, (lo2 + hi2) / 2
    yonly = (p['y'] * p['keep'] + (a['y'] - p['y']) * km.MARG) / a['y']
    rows.append((q, a['keep'], lo, hi, mid, p['keep'], mid2, yonly))
    L.append(f"{q}    {a['keep']:.1%}   {lo:.1%} to {hi:.1%}, {mid:.1%} ({(mid - a['keep']) * 100:+.1f}pt)     "
             f"{p['keep']:.1%} ({(p['keep'] - a['keep']) * 100:+.1f}pt)  {mid2:.1%} ({(mid2 - a['keep']) * 100:+.1f}pt)     {yonly:.1%} ({(yonly - a['keep']) * 100:+.1f}pt)")
err = lambda i: [r[i] - r[1] for r in rows]
mae = lambda i: sum(abs(e) for e in err(i)) / len(rows) * 100
bias = lambda i: sum(err(i)) / len(rows) * 100
L.append('')
L.append(f"Mean miss over {len(rows)} quarters: method {mae(4):.2f}pt (always low, by {-bias(4):.2f}pt on average); same as last quarter {mae(5):.2f}pt; "
         f"method with the yield adjustment {mae(6):.2f}pt; yield adjustment alone {mae(7):.2f}pt")
L.append("Reading: measured flows beat the naive rule. The method runs low because Circle's own platform kept growing in ways the")
L.append("chain doesn't show. Circle's rate table (51.2% of a yield change) made the past four quarters worse: yields fell and the keep rose.")
L.append("Q3-25 is also the quarter Circle's August 2025 Binance wallet deal started; a contract change is the kind of thing this method can't see.")
with open(os.path.join(RESULTS, 'backtest_summary.csv'), 'w') as fh:
    fh.write(f"item,value\nmethod_mae_pt,{mae(4):.3f}\nmethod_bias_pt,{bias(4):.3f}\nnaive_mae_pt,{mae(5):.3f}\nmethod_yield_adj_mae_pt,{mae(6):.3f}\nyield_only_mae_pt,{mae(7):.3f}\nquarters,{len(rows)}\n")
save('backtest_keep.txt', '\n'.join(L) + '\n')
with open(os.path.join(RESULTS, 'backtest_keep.csv'), 'w') as fh:
    fh.write('quarter,actual_keep_pct,method_low_pct,method_high_pct,method_mid_pct,same_as_last_pct,method_with_yield_adj_pct,yield_adj_only_pct\n')
    for r in rows:
        fh.write(f"{r[0]},{r[1] * 100:.2f},{r[2] * 100:.2f},{r[3] * 100:.2f},{r[4] * 100:.2f},{r[5] * 100:.2f},{r[6] * 100:.2f},{r[7] * 100:.2f}\n")
