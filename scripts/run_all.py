# Runs everything in order from any working directory.
import os, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
for s in ['tieout.py', 'yield_split.py', 'reserve_yield.py', 'float_and_tether.py', 'distribution_history.py', 'binance_balances.py', 'insider_sales.py', 'backtest_keep.py', 'hyperliquid_q3.py', 'earnings_power.py', 'beta.py', 'rate_drag.py', 'model.py', 'valuation.py', 'options_check.py', 'reaction_study.py', 'option_odds.py', 'pair_hedge.py', 'rates_float_grid.py', 'peer_multiples.py', 'competition.py', 'usdc_print.py', 'chart_data.py', 'build_workbook.py', 'after_coinbase.py']:
    print('\n=====', s); runpy.run_path(os.path.join(HERE, s), run_name='__main__')
