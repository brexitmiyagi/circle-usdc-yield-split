# The 12-month target across Fed paths (the reserve-return path shifted against the forward curve) and starting USDC float,
# everything else at the base case in valuation.py. Run once with the rate drag and once without.
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import save
with contextlib.redirect_stdout(io.StringIO()):
    import valuation as v

F0 = v.F0
SHIFTS = [-1.50, -1.00, -0.50, 0.0, 0.50, 1.00]
FLOATS = [0.80, 0.90, 1.00, 1.10, 1.20]


def grid(drag):
    out = []
    for s in SHIFTS:
        rp = [max(0.0, x + s) for x in v.FWD]
        row = []
        for k in FLOATS:
            v.F0 = F0 * k
            row.append(v.weighted(rates=rp, drag=drag) * (1 + v.RATE))
        v.F0 = F0
        out.append(row)
    return out


L = [f'12-month target. Rows: reserve return from year 2 ({v.FWD[1]:.2f}% on the curve) shifted by the amount shown. '
     f'Columns: starting USDC as a share of ${F0:.1f}bn.']
csv = ['drag,shift_pt,' + ','.join(f'usdc_{k:.0%}' for k in FLOATS)]
for name, d in (('with the rate drag', v.DRAG), ('no rate drag', 0.0)):
    L.append(name)
    L.append('  shift  ' + ''.join(f'{F0 * k:>9.1f}' for k in FLOATS))
    for s, row in zip(SHIFTS, grid(d)):
        L.append(f'  {s:+.2f}  ' + ''.join(f'{x:9.2f}' for x in row))
        csv.append(f'{d:.3f},{s},' + ','.join(f'{x:.2f}' for x in row))
save('rates_float_grid.txt', '\n'.join(L) + '\n')
with open(os.path.join(HERE, '..', 'results', 'rates_float_grid.csv'), 'w') as f:
    f.write('\n'.join(csv) + '\n')
