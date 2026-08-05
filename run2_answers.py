# Independent second set of answers (Run 2), written fresh from a from-scratch
# pipeline rebuild, without reference to run1_answers.py. Re-indexed here to the
# canonical sample order (matching pipeline.py run against the repository's
# financebench_sample.csv) so index i lines up with prudence_retrieved.json[i]
# regardless of which order either run's own pipeline execution happened to produce.

ANSWERS = {
0: {  # financebench_id_00720
  "C0": "The retrieved context (available-for-sale investment securities and CET1 capital-ratio disclosures) does not discuss gross margin. American Express is a payments/financial-services company, not a manufacturer or retailer, so it does not have a cost-of-goods-sold structure and gross margin is not a metric it reports; performance is instead tracked through revenue, net income, and capital ratios.",
  "C1": "The retrieved context covers investment-securities accounting (credit-loss methodology, fair value) and does not mention gross margin. As a financial-services company, American Express does not have a traditional cost-of-goods-sold structure, so gross margin is not a relevant or reported metric here.",
  "C6": "The retrieved context (banking regulation and deferred-compensation/executive change-in-control provisions) does not address gross margin. Gross margin is not a meaningful metric for American Express because it is a payments/financial-services company without a traditional cost-of-goods-sold structure.",
},
1: {  # financebench_id_00685
  "C0": "Yes, gross margins have been reasonably consistent: gross profit as a percent of revenue was 22.4% in FY2021, 22.5% in FY2022, and 21.4% in FY2023 -- a decline of about 1.1 percentage points from FY2022 to FY2023, within the roughly 2% threshold.",
  "C1": "Yes. Gross profit as a percent of revenue was 22.4% (FY2021), 22.5% (FY2022), and 21.4% (FY2023) -- about a 1.1 percentage point decline from FY2022 to FY2023, so margins have stayed fairly consistent.",
  "C6": "The retrieved context (employee financial-assistance programs and revenue-recognition policy for services/protection plans) does not contain gross margin figures for Best Buy, so consistency cannot be confirmed from this context.",
},
2: {  # financebench_id_01346
  "C0": "The retrieved context shows the reconciliation of unrecognized tax benefits, not the effective-tax-rate reconciliation itself, so the change in effective tax rate cannot be determined from this context.",
  "C1": "The retrieved context discusses unrecognized tax benefits and related audit/settlement activity but does not show the FY2021 or FY2022 effective tax rate, so the change cannot be computed from this context.",
  "C6": "The effective tax rate increased from 20.2% in FY2021 to 22.9% in FY2022 -- an increase of about 2.7 percentage points -- per the statutory-to-effective tax rate reconciliation table.",
},
3: {  # financebench_id_00222
  "C0": "The retrieved context (product-line descriptions and interest-rate market-risk disclosure) does not contain balance sheet figures, so the quick ratio cannot be computed from this context.",
  "C1": "The retrieved context describes AMD's Radeon GPU product line, not balance-sheet data, so cash, receivables, and current liabilities needed for the quick ratio are not available here.",
  "C6": "The retrieved context (NOL/tax-credit carryforward schedules and executive certifications) does not contain balance sheet line items, so the quick ratio cannot be determined from this context.",
},
4: {  # financebench_id_01275
  "C0": "Operating activities generated the most cash in FY2023: $1,824 million provided by operations, compared with $962 million used in investing activities and $1,806 million used in financing activities.",
  "C1": "Operating activities brought in the most cash: $1,824 million from operations in FY2023, versus $962 million used in investing and $1,806 million used in financing activities.",
  "C6": "Operating activities generated the most cash ($1,824 million), compared with cash used in investing (-$962 million) and financing (-$1,806 million).",
},
5: {  # financebench_id_05718
  "C0": "American Water Works paid $389 million in cash dividends during 2020, i.e. approximately $0.39 billion.",
  "C1": "The retrieved context shows the components of operating cash flow (net income, depreciation, working-capital changes) but not a specific cash-dividends-paid line, so the FY2020 dividend amount cannot be determined from this context.",
  "C6": "The retrieved context discusses use of capital resources (including paying dividends) in general terms but does not give the specific FY2020 cash-dividends figure, so the amount cannot be determined from this context.",
},
6: {  # financebench_id_03620
  "C0": "The context shows net income ($8,978M) and depreciation & amortization ($2,763M) from the cash flow statement, and capital spending ($5,207M) from investing activities, but it does not show operating income as a separate line item. Since the question defines unadjusted EBITDA using operating income specifically (not net income), this cannot be precisely computed from the given context.",
  "C1": "The context shows the free-cash-flow reconciliation with capital spending of $5,207 million (FY2022), but it does not show operating income or depreciation and amortization, so unadjusted EBITDA less capex cannot be computed from this context alone.",
  "C6": "The retrieved context (accumulated-other-comprehensive-loss reclassifications and lease disclosures) does not contain operating income, D&A, or capex figures, so this cannot be computed from this context.",
},
7: {  # financebench_id_04672
  "C0": "The retrieved context covers long-term debt schedules and marketable-securities maturities, not balance-sheet property/plant/equipment figures, so net PP&E cannot be determined from this context.",
  "C1": "The retrieved context is the long-term debt and short-term borrowings note, not the balance sheet, so it does not contain the net PP&E figure needed to answer this question.",
  "C6": "The retrieved context covers revenue recognition/disaggregated net sales and derivative netting disclosures, not balance-sheet PP&E, so net PP&E cannot be determined from this context.",
},
8: {  # financebench_id_03029
  "C0": "The retrieved context covers long-term debt schedules and dividend history, not the investing-activities section of the cash flow statement, so the FY2018 capital expenditure amount cannot be determined from this context.",
  "C1": "The retrieved context is a long-term debt and short-term borrowings schedule, not the cash flow statement, so it does not contain the capital expenditure figure requested.",
  "C6": "The retrieved context covers goodwill impairment testing and dividend announcements, not the cash flow statement, so capital expenditure cannot be determined from this context.",
},
9: {  # financebench_id_02049
  "C0": "Yes, it decreased. Average total VaR decreased by $7 million for the three months ended June 30, 2023 compared with the same period a year earlier, driven predominantly by risk reductions in Credit Portfolio VaR and fixed income.",
  "C1": "Yes. Total VaR averaged $47 million in Q2 2023 versus $54 million in Q2 2022, a year-over-year decrease of $7 million, driven mainly by reductions in Credit Portfolio VaR and fixed income risk.",
  "C6": "Yes. Average total VaR decreased by $7 million for the three months ended June 30, 2023 versus the same period in the prior year, driven predominantly by risk reductions in Credit Portfolio VaR and fixed income.",
},
10: {  # financebench_id_00705
  "C0": "PepsiCo increased its unsecured five-year revolving credit agreement by $400,000,000 -- from $3,800,000,000 (2022 Five Year Credit Agreement, terminated) to $4,200,000,000 (2023 Five Year Credit Agreement), effective May 26, 2023.",
  "C1": "PepsiCo entered into a new $4,200,000,000 five-year unsecured revolving credit agreement on May 26, 2023, replacing the prior $3,800,000,000 facility -- an increase of $400,000,000.",
  "C6": "The increase was $400,000,000: PepsiCo terminated its $3,800,000,000 five-year unsecured revolving credit agreement and replaced it with a new $4,200,000,000 five-year unsecured revolving credit agreement on May 26, 2023.",
},
11: {  # financebench_id_01981
  "C0": "The context does not report a specific retention metric, but it describes continued investment in the Delta cobrand partnership, Membership Rewards, and a spend-centric model designed to keep Card Members engaged, which suggests continuity rather than attrition -- though this is inferred, not a stated figure.",
  "C1": "The context does not give an explicit card-member retention figure for 2022; it discusses Card Member attrition risk generally and mentions colleague (employee) retention, not card-member retention specifically, so this cannot be confirmed directly from this context.",
  "C6": "The context does not state a retention rate, but it describes ongoing investment in the Delta cobrand partnership and Membership Rewards aimed at keeping Card Members engaged, which suggests retention was maintained -- though this is inferred rather than a stated figure.",
},
12: {  # financebench_id_01930
  "C0": "Net sales on a comparable constant currency basis were in line with the prior year (i.e., approximately flat) for the twelve months ended June 30, 2023, reflecting roughly 3% price/mix benefit largely offset by roughly 3% lower volumes.",
  "C1": "For the twelve months ended June 30, 2023 vs FY2022, the Comparable Constant Currency Growth was approximately flat (0%) for the total company, per the components table: 1% reported growth, minus ~3% unfavorable FX, plus ~5% raw-material pass-through, minus ~1% comparability items, netting to roughly flat, with volumes down ~3% offset by price/mix up ~3%.",
  "C6": "Net sales on a comparable constant currency basis were in line with the prior year (approximately flat), reflecting roughly 3% price/mix benefit offset by roughly 3% lower volumes.",
},
13: {  # financebench_id_00839
  "C0": "Yes. The incoming CEO, Mary Dillon, most recently served as Executive Chair (and for eight years as CEO) of Ulta Beauty, a large omni-channel beauty retailer -- comparable large-scale brick-and-mortar-plus-digital retail leadership experience to what Foot Locker requires.",
  "C1": "Yes, the new CEO (Mary Dillon) has over 35 years of experience leading consumer-driven businesses and most recently served 8 years as CEO of Ulta Beauty, a comparable large omni-channel retailer that saw a 16% revenue CAGR and tripled market cap under her leadership.",
  "C6": "Yes. Dillon most recently served as CEO of Ulta Beauty for eight years, guiding it to become a leading omni-channel beauty retailer with 16% revenue CAGR and tripled market capitalization -- directly comparable retail leadership experience to what Foot Locker requires.",
},
}
