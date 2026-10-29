# circle-usdc-yield-split

This is the data and code behind my Seeking Alpha piece on Circle (CRCL), "Strip Out The Token Sale And Q3 Earns About 7 Cents A Share". Every number in the piece comes out of a script in here. If you think I got something wrong, run it and show me where.

The short version. Circle and Coinbase split the yield on USDC reserves under a contract that is public (Circle 10-K for 2025, Exhibit 10.1). USDC on Coinbase's platform earns Coinbase the full yield. USDC on Circle's platform earns Circle the full yield. Everything else goes into a shared pool, Circle takes its retention off the top, and Coinbase gets half of what's left. Circle's slice went from 2.2% of USDC in 2024 to 19.5% in the second quarter of 2026, and Coinbase's share of Circle's reserve income fell from 55.7% to 49.6%. But the share going to Binance and Circle's other partners went from 5.2% to 12.2%, and once you adjust for rates Circle keeps about what it kept in 2024. Binance's own monthly reserve reports put what Circle pays Binance at 2.7 to 3.1 cents a year per dollar of USDC Binance held in 2025, against 4.06 cents those dollars earned. Until now that growth paid almost as well as the old float. The newest deal doesn't. Hyperliquid's USDC, about 9% of the total, now sits 90/10 on Coinbase's side of the contract. I measured the split on-chain every day since December 2025. It started on 13 June; before that all of it sat in Circle's own wallet. On those balances Circle's keep goes from 38.5% in Q2 to about 35.7% in Q3. I tested the same method on the four quarters before and it beat the simple "same as last quarter" rule. Q3 GAAP EPS still lands near the Street's, but most of it is a one-off token sale; without it Circle earns about 7 cents. I value the business on three published stablecoin forecasts at weights I set on 27 Oct and get $72 in twelve months; the options market, as a cross-check, gives $84. That's a hold.

## How to run it

Python 3. Every analysis script uses the standard library only; build_workbook.py also needs openpyxl. From any folder:

    python3 scripts/run_all.py

Or one at a time, in the order run_all.py uses. Results land in results/. The spreadsheet is results/circle_model.xlsx; open it in Excel and it recalculates.

## What each script does

- tieout.py checks the inputs against each other and stops if they don't agree. Circle's average USDC against DefiLlama's daily onchain supply. What Circle says it paid Coinbase against what Coinbase says it earned from USDC. Circle's printed reserve return against reserve income over average USDC. The Q2-26 margin against the release.
- yield_split.py splits USDC into the three buckets every quarter (Coinbase's platform, Circle's platform, shared pool), works out Coinbase's share of the shared pool, backs out the deductions Circle takes before the 50/50 split, and prints what the $9.3bn move onto Circle's platform is worth.
- reserve_yield.py reads the Circle Reserve Fund's own monthly SEC filings (N-MFP3) for its daily 7-day yield, measures the gap to Circle's reserve return, and writes down my Q3-26 reserve income estimate before Circle reports.
- float_and_tether.py measures the float side: USDC's peak, its share of all stablecoins, the last 30 days against USDT, the 12-month and 5-year change, and how much of each dollar of float Circle keeps next to Tether.
- distribution_history.py splits Circle's reserve income between Circle, Coinbase and everyone else for 2023, 2024, 2025 and the first half of 2026, adjusts the 2026 keep for rates with Circle's own rate table, bounds what Binance cost Circle in 2025 from the filings, and divides that by Binance's own reported USDC.
- binance_balances.py lines up Binance's monthly proof-of-reserves reports against DefiLlama's on-chain wallet data, checks them against the Binance figures in Circle's prospectus, and measures how much Binance's USDC fell in Q3-26.
- insider_sales.py adds up open-market sales and purchases in Circle's 2026 Form 4 filings.
- keep_method.py holds the keep arithmetic in one place: Hyperliquid's USDC (measured, by address), Binance customers' USDC, and everything else at last quarter's keep.
- backtest_keep.py runs that method on Q3-25 to Q2-26, each quarter from the one before, and compares it with what Circle reported and with "same keep as last quarter". It also tests Circle's rate table as a yield adjustment.
- hyperliquid_q3.py measures the Hyperliquid move. It reads the daily HyperEVM balances of Coinbase's treasury and Circle's Core Deposit Wallet, averages them for Q2 and Q3, adds the legacy Arbitrum bridge from DefiLlama, and works out what Circle keeps and what it pays Coinbase on that USDC. The Q3 keep comes from keep_method.py, plus the backtest's average miss. It also prints the second-half margin Circle's own guidance implies.
- earnings_power.py works out what Circle earns at today's float and yield at the Q2 keep and after Hyperliquid, with per-share sensitivities (rate changes use the 51.2% Circle keeps at the margin, from its own 10-Q rate table).
- beta.py measures CRCL's beta against the S&P 500 on weekly closes and turns it into a cost of equity (CAPM, Blume-adjusted beta, 10-year Treasury, Damodaran's implied equity risk premium). Circle has no debt, so that is the discount rate.
- rate_drag.py estimates how much stablecoin supply higher bill rates cost: monthly change in supply on the change in the 3-month bill over six months, bitcoin held constant, Newey-West errors, all stablecoins and USDC, since 2019 and since 2023, at several lag lengths.
- options_implied.py reads the odds the CRCL options put on any price at an expiry, from a smoothed volatility smile.
- valuation.py values Circle under three published stablecoin forecasts (flat, JPMorgan, Standard Chartered) over ten years. Yields follow the Treasury forward curve less Circle's usual gap to the bill. The float loses the estimated drag for every point the yield sits above today. The keep starts at the measured Q3 level and stays there as yields move (Circle's rate table is a sensitivity). Costs grow at half the float's growth, between 0% and 5%. It adds cash, the Arc stake and Tazapay once. The target uses my weights (35% flat, 55% JPMorgan, 10% Standard Chartered, set 27 Oct). It rolls the value forward a year at the cost of equity, then cross-checks against the options market's odds of CRCL finishing in each scenario's band at the Jan-2028 expiry, and prints the hold range, the 2027 multiples and the sensitivities. It also adds the federal tax losses as a tax shield.
- model.py is the three-statement model: income statement, cash flow and balance sheet for Q3-26 to Q4-27 on the JPMorgan path, with the balance sheet tied out every quarter. It prints the table against consensus for Q3-26, Q4-26, FY26 and FY27, the line-by-line table against Circle's guidance, the Q4 walk, the ARC timing cases, and the 2027 tax rate from the NOL schedule.
- options_check.py reads the CRCL options chain from Cboe and works out what the market pays for: call-spread odds of finishing above each strike, a lognormal check at the implied vol, and the move priced through the 4 November print.
- chart_data.py writes the CSVs behind each chart (chart 8 is the Hyperliquid split).
- build_workbook.py writes the same model to results/circle_model.xlsx with live formulas: assumptions with a source for each, the three statements, the consensus table, the target, the Hyperliquid measurement and the options check. It agrees with model.py to a fraction of a cent.

## Sources

- Circle 10-Qs for Q3-25, Q1-26 and Q2-26, and the FY25 10-K: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001876042
- Coinbase Collaboration Agreement, Circle 10-K FY25 Exhibit 10.1: https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/coinbasecollaborationagree.htm
- Circle Q1-26 and Q2-26 results releases (quarterly tables and guidance)
- Coinbase Q2-26 earnings deck (USDC balances and revenue appendix): https://www.sec.gov/Archives/edgar/data/0001679788/000167978826000087/q226earningsdeck_sec.htm
- Coinbase Q4-25 shareholder letter: https://www.sec.gov/Archives/edgar/data/1679788/000167978826000011/q425shareholderletter.htm
- Circle Reserve Fund N-MFP3 filings, BlackRock Funds (CIK 844779), Dec 2025 to Sep 2026. Accession numbers are in data/circle_reserve_fund_nmfp3.csv.
- DefiLlama stablecoins API for daily USDC, USDT and total supply: https://stablecoins.llama.fi
- US Treasury daily par yield curve: https://home.treasury.gov/resource-center/data-chart-center/interest-rates
- Fed funds target, FRED series DFEDTARU: https://fred.stlouisfed.org/series/DFEDTARU
- 3-month bill for the drag estimate: US Treasury daily par yield curve, 2019 to 2026, averaged by month (data/treasury_3m_monthly.csv): https://home.treasury.gov/resource-center/data-chart-center/interest-rates
- Bitcoin monthly closes: Yahoo Finance, spot-checked against Coinbase Exchange daily candles (data/btc_monthly_yahoo.csv)
- Total stablecoin supply by month: DefiLlama, https://stablecoins.llama.fi
- ARC revenue recognition: Circle 10-Q Q2-26 (ARC Token presale note) and the Q2-26 call. Arc mainnet and the genesis mint: The Block, 16 Sep 2026 (https://www.theblock.co/news/ecosystems/2026-09-16-circle-launches-arc-mainnet-blackrock-and-visa-among-validators-mints-10-billion-arc-tokens-415250)
- Binance agreements (Nov 2024 and the expanded Aug 2025 wallet deal): described in Circle's FY25 10-K, same EDGAR page as above
- SEC staff comment letter to Circle, 11 Apr 2025: https://www.sec.gov/Archives/edgar/data/1876042/000000000025003884/filename2.txt and Circle's reply: https://www.sec.gov/Archives/edgar/data/1876042/000119312525084837/filename1.htm
- Circle Q2-26 earnings call (5 Aug 2026), transcripts at Motley Fool (https://www.fool.com/earnings/call-transcripts/2026/08/12/circle-crcl-q2-2026-earnings-call-transcript/) and gloom.sh (https://gloom.sh/stocks/crcl/transcripts/q2-2026)
- Hyperliquid deal: CoinDesk, 18 May 2026 (https://www.coindesk.com/markets/2026/05/18/hyperliquid-s-usdc-deal-could-supercharge-hype-pressure-circle-coinbase-margins-analysts-say) and JPMorgan via CoinDesk, 14 Jul 2026 (https://www.coindesk.com/business/2026/07/14/jpmorgan-says-hyperliquid-s-rise-threatens-circle-s-usdc-economics)
- Stablecoin forecasts: JPMorgan via The Block (https://www.theblock.co/post/383236/jpmorgan-stablecoin-market-projections); Standard Chartered via The Block (https://www.theblock.co/news/web3/2026-10-14-standard-chartered-stablecoin-market-report-418578)
- Open USD launch: Forbes, 30 Sep 2026 (https://www.forbes.com/sites/gabrielalinzainescu/2026/09/30/ousd-stablecoin-goes-live-with-visa-mastercard-and-stripe-behind-it/)
- Circle IPO prospectus (424B4, 5 Jun 2025), for 2023 and 2024 figures and the $60.25m Binance fee: https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm
- Circle 8-K on the new Binance arrangement and $100m share sale (filed 22 Sep 2026): https://www.sec.gov/Archives/edgar/data/1876042/000187604226000276/crcl-20260917.htm
- Circle 8-K on the CFO transition (filed 25 Sep 2026): https://www.sec.gov/Archives/edgar/data/1876042/000187604226000279/crcl-20260925.htm
- Circle Form 4 filings, 2026: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001876042&type=4
- Binance proof of reserves, monthly snapshots since Jul 2024 (I pulled them from the page's own data feed): https://www.binance.com/en/proof-of-reserves
- DefiLlama, Binance wallets: https://api.llama.fi/protocol/binance-cex
- Tether Q2-26 attestation by BDO, published 31 Jul 2026: https://tether.to/en/transparency/
- Coinbase USDC rewards rate (4.10% APY on 26 Oct 2026, Coinbase One members only since 15 Dec 2025): https://www.coinbase.com/usdc
- Price: Yahoo Finance and Nasdaq, 26 Oct 2026
- HyperEVM balances: USDC contract 0xb88339CB7199b77E23DB6E890353E22632Ba630f, balanceOf at the first block of each day, from two archive RPCs (https://hyperliquid.drpc.org and https://rpc.hyperlend.finance). The public rpc.hyperliquid.xyz ignores the block number, so it can't do history. Address labels are from the HyperEVM explorer (https://hyperevmscan.io).
- DefiLlama bridge data for Hyperliquid's legacy Arbitrum USDC: https://stablecoins.llama.fi
- CRCL options chain, Cboe delayed quotes, 28 Oct 2026: https://cdn.cboe.com/api/global/delayed_quotes/options/CRCL.json
- Prices for the betas: Yahoo Finance daily closes, 2 years to 28 Oct 2026
- Equity risk premium: Damodaran, implied ERP, 1 Oct 2026: https://pages.stern.nyu.edu/~adamodar/
- Consensus: Yahoo Finance earnings trend and Nasdaq's analyst forecast page (Zacks data), both read 28 Oct 2026: https://finance.yahoo.com/quote/CRCL/analysis and https://www.nasdaq.com/market-activity/stocks/crcl/earnings
- Circle 10-K FY25 income tax note (federal NOLs $478.8m, valuation allowance) and 10-Q Q2-26 income taxes note; Circle 8-K on Tazapay (filed 8 Sep 2026) and on the Arc presale (filed 2 Jul 2026): same EDGAR page as the 10-Qs
- FOMC statement, 28 Oct 2026 (held at 3.75% to 4%): https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm

## Things to be careful with

- Coinbase rounds its USDC balances to the nearest $1bn, so every bucket share carries about plus or minus 1.5 points.
- The Issuer Retention tiers are redacted in the filing. The 29 to 44 basis points is my back-out, and it lumps the retention together with payments to approved partners and any cost of capital.
- Q4-25 average USDC and Circle's Q4-25 platform share are derived from the 10-K full-year figures, because Circle didn't print them for the quarter.
- The fund yield is the Circle Reserve Fund only. Circle also holds cash at banks, which is why I take 0.07 to 0.08 points off.
- The valuation weights (35% flat, 55% JPMorgan, 10% Standard Chartered) are my judgement. valuation.py prints the weight the share price implies so you can put in your own. After each forecast's horizon I fade growth from 10% to 3% by year ten; that fade is my choice too.
- The Hyperliquid cost assumes Circle gets nothing extra from Coinbase on the 90%. Circle hasn't disclosed how it splits that deal with Coinbase, so a side payment would make the hit smaller.
- I treat Circle's Core Deposit Wallet as Circle's platform and Coinbase's treasury as Coinbase's, going by the explorer labels and what the CFO said on the Q2 call. Neither company publishes the addresses itself.
- Counting stock pay as a cost is also a choice. Most of the Street works off adjusted EBITDA, which leaves it out.
- I leave the ARC token presale out of earnings on purpose. If Arc turns into recurring fees, that part of my case is wrong.
- The valuation takes yields from the forward curve, which is the market's guess. The curve sits above today's rates, so the float loses 15.6% for every point the reserve return sits above today (rate_drag.py, all stablecoins since 2023, range 12.3% to 19.0%). That's a correlation in monthly data, not a proven cause. The full sample back to 2019 gives 24%, mostly because of 2022. With no drag the value is about $90, at 24% about $67.
- The target weights are mine and they're a judgement. The options market is the outside check; its odds are risk-neutral, so they lean to bad outcomes, and they track the share price by design.
- The 2027 tax rate (about 17%) comes from running the $478.8m of federal NOLs down at the 80% limit, treating book pretax as taxable income. That ignores further stock-pay deductions, so it leans high. A valuation-allowance release would be a one-off gain and is left out.
- Consensus adjusted EBITDA, RLDC and distribution costs aren't on free sources. results/table_line_items.csv sets my lines next to Circle's FY26 guidance, and model.txt backs out what the Street's Q4 EPS implies. I can't place about $32m of the Q4 gap.
- Every scenario holds USDC's share of stablecoins at today's 23.7%. It was 24.6% on the Q2 average. valuation.py prints the value if USDC loses half a point or a full point of share a year (target about $59 and $45).
- The headline Q3 number is scored as (GAAP net income attributable to common - ARC token revenue x (1 - the quarter's effective tax rate)) / diluted shares; model.py prints the range ($0.01 to $0.13).
- The keep backtest covers only four quarters. The method ran about half a point low every time, and I add that back. It can't see contract changes like the August 2025 Binance deal.
- Circle's rate table says it keeps 51.2% of a change in yield. The backtest did worse with it, so the base case holds the keep flat as yields move. Switch use_rate_table_for_keep to 1 in data/model_assumptions.csv to use it; it adds about $9 a share.
- ARC token revenue is booked as milestones are met. Circle guided about $180m for 2026 but hasn't said which quarter; I split it evenly over Q3 and Q4. Each $10m moves quarterly EPS by about 3.5 cents. model.py prints Q3 at $0, $90m and $180m.
- The 12-month target is today's value rolled forward a year at the cost of equity. It is not a forecast of where the stock trades.
- The Arc stake is 25% of the $3bn presale valuation, a price set by a token sale, not a market. At half that the value drops by about $1.40 a share.
- The three-statement model holds every balance sheet line it doesn't forecast at its 30 June level, and ARC token revenue in Q3 and Q4 is my split of the ~$180m Circle expects for 2026. The 2027 tax rate is the 21% statutory rate; Circle paid 5.1% in the first half.
- Tether's number is operating profit before marks on its bitcoin and gold, and Tether is not audited the way Circle is. Treat the comparison as a rough size check.
- Circle never prints a Binance cost line. The $212m to $238m for 2025 is a bound: 2024's Binance cost was at least the $60.25m upfront fee and at most all of 2024's non-Coinbase partner costs, and the 10-K gives the $152.1m increase.
- The per-dollar Binance cost divides that by the USDC Binance reports holding. Circle's fee is on USDC "held through" its wallet service, which may not be the same base. A bigger base means a lower rate.
- Circle's 10-K restated 2024 Coinbase costs to $924.5m (the prospectus said $907.9m). I use the 10-K for 2024 onward and the prospectus only for 2023.
- The rate adjustment applies Circle's June 2026 rate table to the whole first half of 2026. It's an approximation.
- The "rest of Circle's platform" split assumes all of Binance's customer USDC sits on Circle's side of the contract. Circle doesn't say.

## Corrections

None so far.
