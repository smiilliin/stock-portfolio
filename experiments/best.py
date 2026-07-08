from experiments.ratio import run_ratio_experiment
import pandas as pd

"""
VVV	VOO + VXUS + VGIT
VSV	VOO + SCHD + VGIT
VTV	VTI + VXUS + VGIT
SVV	SCHD + VXUS + VGIT
VV	VOO + VGIT
VS	VOO + SCHD
"""

COMBS = {
    "vsv": ["VTI", "SCHD", "VGIT"],
    "vsvg": ["VTI", "SCHD", "VGIT", "GLD"],
    "vsvi": ["VTI", "SCHD", "VGIT", "IAU"],
    # --------------------------------------#
    "vts": ["VTI", "SCHD", "VGIT"],
    "vtst": ["VTI", "SCHD", "TLT"],
    "vtss": ["VTI", "SCHD", "SGOV"],
    "vv": ["VOO", "VGIT"],
    "vs": ["VOO", "SCHD"],
    "vt": ["VOO", "VXUS"],
    "vvv": ["VOO", "VXUS", "VGIT"],
    "svv": ["SCHD", "VXUS", "VGIT"],
    "vtv": ["VTI", "VXUS", "VGIT"],
    "vvs": ["VOO", "VXUS", "SCHD"],
    "vvsg": ["VOO", "VXUS", "SCHD", "GLD"],
    "us1": ["VOO", "SCHD", "VTI"],
    "taa": ["KR7360750004", "KR7453850000", "KR7411060007"],
    "growth": ["VOO", "SCHD", "VGIT"],
    "global": ["VOO", "VXUS", "VGIT"],
    "equity1": ["VOO", "SCHD", "VXUS"],
    "equity2": ["VOO", "SCHD", "VXUS", "VGIT"],
}


def run_best_experiment(
    combination_list,
    start_date,
    end_date,
    monthly_investment,
    step=0.1,
    no_zero_ratio=False,
):
    bests = []

    for comb in combination_list:
        tickers = COMBS[comb]
        if not tickers:
            raise ValueError(f"Combination {comb} not found in COMBS dictionary")

        print(f"Running experiment for combination: {comb} with tickers: {tickers}")

        _, df_frontier = run_ratio_experiment(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            monthly_investment=monthly_investment,
            score_weights=[0.30, 0.20, 0.25, 0.25],
            no_zero_ratio=no_zero_ratio,
            step=step,
            percent=False,
        )
        df_frontier.sort_values(by="score", ascending=False, inplace=True)

        df_frontier.insert(0, "combination", "+".join(tickers))

        best = df_frontier.iloc[0]
        bests.append(best)

    return pd.DataFrame(bests).reset_index(drop=True)
