#!/usr/bin/env python
# coding: utf-8


import dataframe_image as dfi

from experiments.ratio2 import run_ratio2_experiment, visualize_ratio2_result
from modules.parser import build_argument_parser

from experiments.strategy import (
    visualize_strategy_histories,
    run_strategy_experiment,
)
from experiments.ratio import (
    highlight_ranking,
    run_ratio_experiment,
    visualize_ratio_result,
)


def parse_csv_values(raw_value: str, cast_type):
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return [cast_type(value) for value in values]


def build_output_name(base_name: str, suffix: str, extension: str):
    global output_dir
    safe_suffix = suffix.strip().replace(" ", "_")
    if not safe_suffix:
        return f"./{output_dir}/{base_name}.{extension}"

    return f"./{output_dir}/{base_name}_{safe_suffix}.{extension}"


import json
from pathlib import Path
from types import SimpleNamespace

DEFAULTS = {
    "tickers": None,
    "output": "./output",
    "mode": "strategy",
    "step": 0.1,
    "combs": None,
    "no_zero_ratio": False,
    "portfolio_ratio": None,
    "output_suffix": "",
    "start_date": "2000-01-01",
    "end_date": "2026-07-01",
    "monthly_investment": 300,
}


def load_config(args):
    config = {}

    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

    settings = {}

    for key, default in DEFAULTS.items():
        cli_value = getattr(args, key)

        # argparse에서 기본값 그대로면 config 사용
        if cli_value == default:
            settings[key] = config.get(key, default)
        else:
            settings[key] = cli_value

    return SimpleNamespace(**settings)


def main():
    global output_dir

    args = build_argument_parser().parse_args()
    cfg = load_config(args)

    output_dir = cfg.output
    if cfg.tickers:
        tickers = parse_csv_values(cfg.tickers, str)
    if cfg.combs:
        combs = parse_csv_values(cfg.combs, str)
    if cfg.no_zero_ratio:
        no_zero_ratio = True
    else:
        no_zero_ratio = False

    mode = cfg.mode.lower()
    output_suffix = cfg.output_suffix
    start_date = cfg.start_date
    end_date = cfg.end_date
    monthly_investment = cfg.monthly_investment
    step = cfg.step

    if mode == "strategy":
        if not cfg.tickers:
            raise ValueError("--tickers must have some values")

        if cfg.portfolio_ratio is None:
            raise ValueError("--tickers and --portfolio-ratio must have some values")

        portfolio_ratio = parse_csv_values(cfg.portfolio_ratio, float)

        if len(tickers) != len(portfolio_ratio):
            raise ValueError(
                "--tickers and --portfolio-ratio must have the same length"
            )

        strategy_histories, summary_df, every_month_date = run_strategy_experiment(
            tickers=tickers,
            portfolio_ratio=portfolio_ratio,
            start_date=start_date,
            end_date=end_date,
            monthly_investment=monthly_investment,
        )

        summary_output_path_png = build_output_name(
            "strategy_summary", output_suffix, "png"
        )
        dfi.export(summary_df, summary_output_path_png, table_conversion="matplotlib")
        print(f"Strategy summary saved to {summary_output_path_png}")

        comparison_output_path_png = build_output_name(
            "strategy_comparison", output_suffix, "png"
        )
        visualize_strategy_histories(
            output_path=comparison_output_path_png,
            strategy_histories=strategy_histories,
            every_month_date=every_month_date,
            monthly_investment=monthly_investment,
            title=f"Strategy Comparison {output_suffix}".strip(),
        )

    elif mode == "ratio":
        if not cfg.tickers:
            raise ValueError("--tickers must have some values")

        df, df_frontier = run_ratio_experiment(
            start_date=start_date,
            tickers=tickers,
            end_date=end_date,
            monthly_investment=monthly_investment,
            step=step,
            no_zero_ratio=no_zero_ratio,
        )

        styled = df.style.apply(highlight_ranking, df_frontier=df_frontier, axis=None)

        ratio_output_path_png = build_output_name("ratio_data", output_suffix, "png")
        styled.hide(axis="index")
        dfi.export(styled, ratio_output_path_png, table_conversion="matplotlib")

        print(f"Ratio data saved to {ratio_output_path_png}")

        ratio_vis_path_png = build_output_name("ratio_vis", output_suffix, "png")

        visualize_ratio_result(
            df=df,
            df_frontier=df_frontier,
            output_path=ratio_vis_path_png,
            title=f"Portfolio Ratio Experiment {output_suffix}".strip(),
        )
    elif mode == "ratio2":
        if not cfg.tickers:
            raise ValueError("--tickers must have some values")

        df = run_ratio2_experiment(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            monthly_investment=monthly_investment,
            step=step,
        )
        df.sort_values(by="score", ascending=False, inplace=True)
        # get average of top 20 df
        # df = df.head(20)

        # styled = df.style.apply(highlight_ranking, df_frontier=df_frontier, axis=None)

        # ratio_output_path_png = build_output_name("ratio2_data", output_suffix, "png")
        # dfi.export(df, ratio_output_path_png, table_conversion="matplotlib")

        # print(f"Ratio data saved to {ratio_output_path_png}")

        ratio_vis_path_png = build_output_name("ratio2_vis", output_suffix, "png")

        visualize_ratio2_result(
            df=df,
            tickers=tickers,
            output_path=ratio_vis_path_png,
            title=f"Portfolio Ratio Experiment {output_suffix}".strip(),
        )
    elif mode == "best":
        from experiments.best import run_best_experiment

        if not cfg.combs:
            raise ValueError("--combs must have some values")

        best_df = run_best_experiment(
            combination_list=combs,
            start_date=start_date,
            end_date=end_date,
            monthly_investment=monthly_investment,
            step=step,
            no_zero_ratio=no_zero_ratio,
        )
        best_df = best_df.drop(columns=["score"])

        best_output_path_png = build_output_name("best_data", output_suffix, "png")
        styled = best_df.style.apply(highlight_ranking, axis=None, no_score_column=True)
        styled = styled.hide(axis="index")
        # best_df.
        dfi.export(styled, best_output_path_png, table_conversion="matplotlib")

        print(f"Best data saved to {best_output_path_png}")

    else:
        raise ValueError(f"Unknown mode: {mode}")

    # raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
