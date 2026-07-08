import argparse

default_every_month_investment = 300


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Run stock portfolio simulations.")
    parser.add_argument(
        "--tickers",
        help="Comma-separated tickers to simulate, for example VOO,VXUS,TLT",
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory for saved files",
    )
    parser.add_argument(
        "--config",
        default="./config.json",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--mode",
        default="strategy",
        help="Simulation mode: 'strategy', 'ratio', 'best'",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.1,
        help="Step size for generating portfolio ratios",
    )
    parser.add_argument(
        "--combs",
        help="Comma-separated combinations of tickers to simulate, for example vvv,vsv,vtv,svv,vv,vs",
    )
    parser.add_argument(
        "--no-zero-ratio",
        action="store_true",
        help="Exclude portfolio ratios with zero weights",
    )
    parser.add_argument(
        "--portfolio-ratio",
        help="Comma-separated portfolio ratios that match --tickers",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="Suffix to append to saved files, for example core or test01",
    )
    parser.add_argument(
        "--start-date",
        default="2000-01-01",
        help="Historical data start date",
    )
    parser.add_argument(
        "--end-date",
        default="2026-07-01",
        help="Historical data end date",
    )
    parser.add_argument(
        "--monthly-investment",
        type=float,
        default=default_every_month_investment,
        help="Amount invested each month",
    )
    return parser
